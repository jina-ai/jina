import asyncio
import argparse
from typing import (
    List,
    Union,
    Iterator,
    AsyncIterator,
    TYPE_CHECKING,
    Callable,
    Optional,
)

from .helper import AsyncRequestsIterator
from ...logging.logger import JinaLogger
from ...types.message import Message

__all__ = ['RequestStreamer']

if TYPE_CHECKING:
    from ...types.request import Request


class RequestStreamer:
    """
    A base async request/response streamer.
    """

    def __init__(
        self,
        args: argparse.Namespace,
        request_handler: Callable[['Request'], 'asyncio.Future'],
        result_handler: Callable[
            [Union['Request', 'Message', List['Message']]], Optional['Request']
        ],
        logger: Optional['JinaLogger'] = None,
        end_of_iter_handler: Optional[Callable[[], None]] = None,
    ):
        """
        :param args: args from CLI
        :param request_handler: The callable responsible for handling the request. It should handle a request as input and return a Future to be awaited
        :param result_handler: The callable responsible for handling the response.
        :param logger: Optional logger that can be used for logging
        :param end_of_iter_handler: Optional callable to handle the end of iteration if some special action needs to be taken.
        """
        self.args = args
        self.logger = logger or JinaLogger(self.__class__.__name__, **vars(args))
        self._prefetch = getattr(self.args, 'prefetch', 0)
        self._request_handler = request_handler
        self._result_handler = result_handler
        self._end_of_iter_handler = end_of_iter_handler

    async def stream(self, request_iterator, *args) -> AsyncIterator['Request']:
        """
        stream requests from client iterator and stream responses back.

        :param request_iterator: iterator of requests
        :param args: positional arguments
        :yield: responses from Executors
        """
        async_iter: AsyncIterator = (
            self._stream_requests_with_prefetch(request_iterator, self._prefetch)
            if self._prefetch > 0
            else self._stream_requests(request_iterator)
        )

        async for response in async_iter:
            yield response

    async def _stream_requests(
        self, request_iterator: Union[Iterator, AsyncIterator]
    ) -> AsyncIterator:
        """Implements request and response handling without prefetching
        :param request_iterator: requests iterator from Client
        :yield: responses
        """
        result_queue = asyncio.Queue()
        end_of_iter = asyncio.Event()
        futures = []

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
            futures.remove(future)

        async def iterate_requests() -> None:
            """
            1. Traverse through the request iterator.
            2. `add_done_callback` to the future returned by `handle_request`.
                This callback adds the completed future to `result_queue`
            3. Append future to list of futures.
            4. Handle EOI (needed for websocket client)
            5. Set `end_of_iter` event
            """
            async for request in AsyncRequestsIterator(iterator=request_iterator):
                future: 'asyncio.Future' = self._request_handler(request=request)
                future.add_done_callback(callback)
                futures.append(future)
            if self._end_of_iter_handler is not None:
                self._end_of_iter_handler()
            end_of_iter.set()

        asyncio.create_task(iterate_requests())
        while not end_of_iter.is_set() or len(futures) > 0 or not result_queue.empty():
            # `not end_of_iter.is_set()` validates iterator is completed.
            # `len(futures) > 0` makes sure all futures are taken care of.
            # `not result_queue.empty()` makes sure all items in queue are processed.
            try:
                response: 'asyncio.Future' = result_queue.get_nowait()
                yield self._result_handler(response.result())
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.01)

    async def _stream_requests_with_prefetch(
        self, request_iterator: Union[Iterator, AsyncIterator], prefetch: int
    ):
        """Implements request and response handling with prefetching

        :param request_iterator: requests iterator from Client
        :param prefetch: number of requests to prefetch
        :yield: response
        """

        async def iterate_requests(
            num_req: int, fetch_to: List[Union['asyncio.Task', 'asyncio.Future']]
        ):
            """
            1. Traverse through the request iterator.
            2. Append the future returned from `handle_request` to `fetch_to` which will later be awaited.

            :param num_req: number of requests
            :param fetch_to: the task list storing requests
            :return: False if append task to `fetch_to` else False
            """
            count = 0
            async for request in AsyncRequestsIterator(iterator=request_iterator):
                fetch_to.append(self._request_handler(request))
                count += 1
                if count == num_req:
                    return False
            return True

        prefetch_task = []
        is_req_empty = await iterate_requests(prefetch, prefetch_task)
        if is_req_empty and not prefetch_task:
            self.logger.error(
                'receive an empty stream from the client! '
                'please check your client\'s inputs, '
                'you can use "Client.check_input(inputs)"'
            )
            return

        # the total num requests < prefetch
        if is_req_empty:
            for r in asyncio.as_completed(prefetch_task):
                res = await r
                yield self._result_handler(res)
        else:
            # if there are left over (`else` clause above is unnecessary for code but for better readability)
            onrecv_task = []
            # the following code "interleaves" prefetch_task and onrecv_task, when one dries, it switches to the other
            while prefetch_task:
                # if self.logger.debug_enabled:
                #     if hasattr(self.msg_handler, 'msg_sent') and hasattr(
                #         self.msg_handler, 'msg_recv'
                #     ):
                #         self.logger.debug(
                #             f'send: {self.msg_handler.msg_sent} '
                #             f'recv: {self.msg_handler.msg_recv} '
                #             f'pending: {self.msg_handler.msg_sent - self.msg_handler.msg_recv}'
                #         )
                onrecv_task.clear()
                for r in asyncio.as_completed(prefetch_task):
                    res = await r
                    yield self._result_handler(res)
                    if not is_req_empty:
                        is_req_empty = await iterate_requests(1, onrecv_task)

                # this list dries, clear it and feed it with on_recv_task
                prefetch_task.clear()
                prefetch_task = [j for j in onrecv_task]
