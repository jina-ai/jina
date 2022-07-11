import argparse
import asyncio
from typing import (
    TYPE_CHECKING,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterator,
    List,
    Optional,
    Union,
)

from jina.excepts import InternalNetworkError
from jina.logging.logger import JinaLogger
from jina.serve.stream.helper import AsyncRequestsIterator, RequestsCounter

__all__ = ['RequestStreamer']

from jina.types.request.data import Response

if TYPE_CHECKING:
    from jina.types.request import Request


class RequestStreamer:
    """
    A base async request/response streamer.
    """

    class _EndOfStreaming(Exception):
        pass

    def __init__(
        self,
        args: argparse.Namespace,
        request_handler: Callable[['Request'], 'Awaitable[Request]'],
        result_handler: Callable[['Request'], Optional['Request']],
        end_of_iter_handler: Optional[Callable[[], None]] = None,
        logger: Optional['JinaLogger'] = None,
    ):
        """
        :param args: args from CLI
        :param request_handler: The callable responsible for handling the request. It should handle a request as input and return a Future to be awaited
        :param result_handler: The callable responsible for handling the response.
        :param end_of_iter_handler: Optional callable to handle the end of iteration if some special action needs to be taken.
        :param logger: Optional logger that can be used for logging

        """
        self.args = args
        self.logger = logger or JinaLogger(self.__class__.__name__, **vars(args))
        self._prefetch = getattr(self.args, 'prefetch', 0)
        self._request_handler = request_handler
        self._result_handler = result_handler
        self._end_of_iter_handler = end_of_iter_handler

    async def stream(
        self, request_iterator, context=None, *args
    ) -> AsyncIterator['Request']:
        """
        stream requests from client iterator and stream responses back.

        :param request_iterator: iterator of requests
        :param context: context of the grpc call
        :param args: positional arguments
        :yield: responses from Executors
        """

        async_iter: AsyncIterator = self._stream_requests(request_iterator)

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
                raise

    async def _stream_requests(
        self,
        request_iterator: Union[Iterator, AsyncIterator],
    ) -> AsyncIterator:
        """Implements request and response handling without prefetching
        :param request_iterator: requests iterator from Client
        :yield: responses
        """
        result_queue = asyncio.Queue()
        hanging_queue = asyncio.Queue()
        end_of_iter = asyncio.Event()
        all_requests_handled = asyncio.Event()
        requests_to_handle = RequestsCounter()
        hanging_tasks_to_handle = RequestsCounter()
        all_hanging_requests_awaited = asyncio.Event()

        def update_all_handled():
            if end_of_iter.is_set() and requests_to_handle.count == 0:
                all_requests_handled.set()

        async def end_future():
            raise self._EndOfStreaming

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
            hanging_queue.put_nowait(future)

        async def iterate_requests() -> None:
            """
            1. Traverse through the request iterator.
            2. `add_done_callback` to the future returned by `handle_request`.
                This callback adds the completed future to `result_queue`
            3. Append future to list of futures.
            4. Handle EOI (needed for websocket client)
            5. Set `end_of_iter` event
            """
            async for request in AsyncRequestsIterator(
                iterator=request_iterator,
                request_counter=requests_to_handle,
                prefetch=self._prefetch,
            ):
                requests_to_handle.count += 1
                future, future_hanging = self._request_handler(request=request)
                future.add_done_callback(callback)
                if future_hanging is not None:
                    hanging_tasks_to_handle.count += 1
                    future_hanging.add_done_callback(hanging_callback)
                else:
                    all_hanging_requests_awaited.set()

            if self._end_of_iter_handler is not None:
                self._end_of_iter_handler()
            end_of_iter.set()
            update_all_handled()
            if all_requests_handled.is_set():
                # It will be waiting for something that will never appear
                future_cancel = asyncio.ensure_future(end_future())
                result_queue.put_nowait(future_cancel)

        async def handle_hanging_tasks():
            while not all_hanging_requests_awaited.is_set():
                _ = await hanging_queue.get()
                hanging_tasks_to_handle.count -= 1
                if hanging_tasks_to_handle.count == 0 and all_requests_handled.is_set():
                    all_hanging_requests_awaited.set()

        asyncio.create_task(iterate_requests())
        hanging_hanging_tasks = asyncio.create_task(handle_hanging_tasks())

        while not all_requests_handled.is_set():
            future = await result_queue.get()
            try:
                response = self._result_handler(future.result())
                yield response
                requests_to_handle.count -= 1
                update_all_handled()
            except self._EndOfStreaming:
                pass

        await hanging_hanging_tasks
