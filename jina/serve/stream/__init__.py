import asyncio
from typing import (
    TYPE_CHECKING,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterator,
    Optional,
    Union,
)

from jina.excepts import InternalNetworkError
from jina.logging.logger import JinaLogger
from jina.serve.stream.helper import AsyncRequestsIterator, _RequestsCounter
from jina.types.request.data import DataRequest

__all__ = ['RequestStreamer']

from jina.types.request.data import Response

if TYPE_CHECKING:  # pragma: no cover
    from jina.types.request import Request


class RequestStreamer:
    """
    A base async request/response streamer.
    """

    class _EndOfStreaming(Exception):
        pass

    def __init__(
        self,
        request_handler: Callable[['Request'], 'Awaitable[Request]'],
        result_handler: Callable[['Request'], Optional['Request']],
        prefetch: int = 0,
        end_of_iter_handler: Optional[Callable[[], None]] = None,
        logger: Optional['JinaLogger'] = None,
        **logger_kwargs,
    ):
        """
        :param request_handler: The callable responsible for handling the request. It should handle a request as input and return a Future to be awaited
        :param result_handler: The callable responsible for handling the response.
        :param end_of_iter_handler: Optional callable to handle the end of iteration if some special action needs to be taken.
        :param prefetch: How many Requests are processed from the Client at the same time.
        :param logger: Optional logger that can be used for logging
        :param logger_kwargs: Extra keyword arguments that may be passed to the internal logger constructor if none is provided

        """
        self.logger = logger or JinaLogger(self.__class__.__name__, **logger_kwargs)
        self._prefetch = prefetch
        self._request_handler = request_handler
        self._result_handler = result_handler
        self._end_of_iter_handler = end_of_iter_handler
        self.total_num_floating_tasks_alive = 0

    async def stream(
        self, request_iterator, context=None, results_in_order: bool = False, *args
    ) -> AsyncIterator['Request']:
        """
        stream requests from client iterator and stream responses back.

        :param request_iterator: iterator of requests
        :param context: context of the grpc call
        :param results_in_order: return the results in the same order as the request_iterator
        :param args: positional arguments
        :yield: responses from Executors
        """
        if context is not None:
            for metadatum in context.invocation_metadata():
                if metadatum.key == '__results_in_order__':
                    results_in_order = metadatum.value == 'true'

        async_iter: AsyncIterator = self._stream_requests(
            request_iterator=request_iterator, results_in_order=results_in_order
        )

        try:
            async for response in async_iter:
                yield response
        except InternalNetworkError as err:
            if (
                context is not None
            ):  # inside GrpcGateway we can handle the error directly here through the grpc context
                context.set_details(err.details())
                context.set_code(err.code())
                self.logger.error(
                    f'Error while getting responses from deployments: {err.details()}'
                )
                r = Response()
                if err.request_id:
                    r.header.request_id = err.request_id
                yield r
            else:  # HTTP and WS need different treatment further up the stack
                self.logger.error(
                    f'Error while getting responses from deployments: {err.details()}'
                )
                raise
        except Exception as err:  # HTTP and WS need different treatment further up the stack
            self.logger.error(f'Error while getting responses from deployments: {err}')
            raise err

    async def _stream_requests(
        self,
        request_iterator: Union[Iterator, AsyncIterator],
        results_in_order: bool = False,
    ) -> AsyncIterator:
        """Implements request and response handling without prefetching
        :param request_iterator: requests iterator from Client
        :param results_in_order: return the results in the same order as the request_iterator
        :yield: responses
        """
        result_queue = asyncio.Queue()
        future_queue = asyncio.Queue()
        floating_results_queue = asyncio.Queue()
        end_of_iter = asyncio.Event()
        all_requests_handled = asyncio.Event()
        requests_to_handle = _RequestsCounter()
        floating_tasks_to_handle = _RequestsCounter()
        all_floating_requests_awaited = asyncio.Event()
        empty_requests_iterator = asyncio.Event()

        def update_all_handled():
            if end_of_iter.is_set() and requests_to_handle.count == 0:
                all_requests_handled.set()

        async def end_future():
            raise self._EndOfStreaming

        async def exception_raise(exception):
            raise exception

        def callback(future: 'asyncio.Future'):
            """callback to be run after future is completed.
            1. Put the future in the result queue.
            2. Remove the future from futures when future is completed.
            ..note::
                callback cannot be an awaitable, hence we cannot do `await queue.put(...)` here.
                We don't add `future.result()` to the queue, as that would consume the exception in the callback,
                which is difficult to handle.
            :param future: asyncio Future object retured from `handle_response`
            """
            result_queue.put_nowait(future)

        def hanging_callback(future: 'asyncio.Future'):
            floating_results_queue.put_nowait(future)

        async def iterate_requests() -> None:
            """
            1. Traverse through the request iterator.
            2. `add_done_callback` to the future returned by `handle_request`.
                This callback adds the completed future to `result_queue`
            3. Append future to list of futures.
            4. Handle EOI (needed for websocket client)
            5. Set `end_of_iter` event
            """
            num_reqs = 0
            async for request in AsyncRequestsIterator(
                iterator=request_iterator,
                request_counter=requests_to_handle,
                prefetch=self._prefetch,
            ):
                num_reqs += 1
                requests_to_handle.count += 1
                future_responses, future_hanging = self._request_handler(
                    request=request
                )
                future_queue.put_nowait(future_responses)
                future_responses.add_done_callback(callback)
                if future_hanging is not None:
                    floating_tasks_to_handle.count += 1
                    future_hanging.add_done_callback(hanging_callback)
                else:
                    all_floating_requests_awaited.set()

            if num_reqs == 0:
                empty_requests_iterator.set()

            if self._end_of_iter_handler is not None:
                self._end_of_iter_handler()
            end_of_iter.set()
            update_all_handled()
            if all_requests_handled.is_set():
                # It will be waiting for something that will never appear
                future_cancel = asyncio.ensure_future(end_future())
                result_queue.put_nowait(future_cancel)
            if (
                all_floating_requests_awaited.is_set()
                or empty_requests_iterator.is_set()
            ):
                # It will be waiting for something that will never appear
                future_cancel = asyncio.ensure_future(end_future())
                floating_results_queue.put_nowait(future_cancel)

        async def handle_floating_responses():
            while (
                not all_floating_requests_awaited.is_set()
                and not empty_requests_iterator.is_set()
            ):
                hanging_response = await floating_results_queue.get()
                try:
                    hanging_response.result()
                    floating_tasks_to_handle.count -= 1
                    if floating_tasks_to_handle.count == 0 and end_of_iter.is_set():
                        all_floating_requests_awaited.set()
                except self._EndOfStreaming:
                    pass

        iterate_requests_task = asyncio.create_task(iterate_requests())
        handle_floating_task = asyncio.create_task(handle_floating_responses())
        self.total_num_floating_tasks_alive += 1

        def floating_task_done(*args):
            self.total_num_floating_tasks_alive -= 1

        handle_floating_task.add_done_callback(floating_task_done)

        def iterating_task_done(task):
            if task.exception() is not None:
                all_requests_handled.set()
                future_cancel = asyncio.ensure_future(exception_raise(task.exception()))
                result_queue.put_nowait(future_cancel)

        iterate_requests_task.add_done_callback(iterating_task_done)

        async def receive_responses():
            while not all_requests_handled.is_set():
                if not results_in_order:
                    future = await result_queue.get()
                else:
                    future = await future_queue.get()
                    await future
                try:
                    response = self._result_handler(future.result())
                    yield response
                    requests_to_handle.count -= 1
                    update_all_handled()
                except self._EndOfStreaming:
                    pass

        async for response in receive_responses():
            yield response

    async def wait_floating_requests_end(self):
        """
        Await this coroutine to make sure that all the floating tasks that the request handler may bring are properly consumed
        """
        while self.total_num_floating_tasks_alive > 0:
            await asyncio.sleep(0)
