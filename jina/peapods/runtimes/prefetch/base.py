import argparse
import asyncio
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Union, TYPE_CHECKING, Dict, Awaitable

from ....helper import typename, get_or_reuse_loop
from ....logging.logger import JinaLogger
from ....types.message import Message

__all__ = ['BasePrefetcher']

if TYPE_CHECKING:
    from ...grpc import Grpclet
    from ...zmq import AsyncZmqlet
    from ....types.request import Request, Response
    from ....clients.base.helper import HTTPClientlet, WebsocketClientlet


class BasePrefetcher(ABC):
    """An base async request/response handler"""

    def __init__(
        self,
        args: argparse.Namespace,
        iolet: Union['AsyncZmqlet', 'Grpclet', 'HTTPClientlet', 'WebsocketClientlet'],
    ):
        """
        :param args: args from CLI
        :param iolet: One of AsyncZmqlet or Grpclet. Used for sending/receiving data to/from the Flow
        """
        self.args = args
        self.iolet = iolet
        self.logger = JinaLogger(self.__class__.__name__, **vars(args))
        self.request_buffer: Dict[str, asyncio.Future] = dict()
        self.receive_task = get_or_reuse_loop().create_task(self.receive())

    @abstractmethod
    async def receive(self) -> Awaitable:
        """Receive background task"""
        ...

    @abstractmethod
    def convert_to_message(self, request: 'Request') -> Union['Message', 'Request']:
        """Convert request to iolet message

        :param request: current request in the iterator
        """
        ...

    def handle_request(self, request: 'Request') -> 'asyncio.Future':
        """
        For ZMQ & GRPC data requests, for each request in the iterator, we send the `Message` using
        `iolet.send_message()` and add {<request-id>: <an-empty-future>} to the message buffer.
        This empty future is used to track the `result` of this request during `receive`.

        :param request: current request in the iterator
        :return: asyncio Future for sending message
        """
        future = get_or_reuse_loop().create_future()
        self.request_buffer[request.request_id] = future
        asyncio.create_task(self.iolet.send_message(self.convert_to_message(request)))
        return future

    def handle_response(self, response: 'Response'):
        """Set result of each response received in the request buffer

        :param response: message received during `iolet.recv_message`
        """
        if response.request_id in self.request_buffer:
            future = self.request_buffer.pop(response.request_id)
            future.set_result(response)
        else:
            self.logger.warning(
                f'Discarding unexpected response with request id {response.request_id}'
            )

    @abstractmethod
    def handle_end_of_iter(self):
        """Manage end of iteration if required"""
        ...

    async def close(self):
        """
        Stop receiving messages
        """
        self.receive_task.cancel()

    async def send(self, request_iterator, *args) -> AsyncGenerator[None, Message]:
        """
        Async call to receive Requests and build them into Messages.

        :param request_iterator: iterator of requests.
        :param args: additional arguments
        :yield: message
        """
        if self.receive_task.done():
            raise RuntimeError(
                'Prefetcher receive task not running, can not send messages'
            )

        async def prefetch_req(
            num_req: int, fetch_to: List[Union['asyncio.Task', 'asyncio.Future']]
        ):
            """
            Fetch and send request.

            :param num_req: number of requests
            :param fetch_to: the task list storing requests
            :return: False if append task to :param:`fetch_to` else False
            """
            for _ in range(num_req):
                try:
                    if hasattr(request_iterator, '__anext__'):
                        request = await request_iterator.__anext__()
                    elif hasattr(request_iterator, '__next__'):
                        request = next(request_iterator)
                    else:
                        raise TypeError(
                            f'{typename(request_iterator)} does not have `__anext__` or `__next__`'
                        )

                    fetch_to.append(self.handle_request(request=request))
                except (StopIteration, StopAsyncIteration):
                    self.handle_end_of_iter()
                    return True
            return False

        prefetch_task = []
        is_req_empty = await prefetch_req(self.args.prefetch, prefetch_task)
        if is_req_empty and not prefetch_task:
            self.logger.error(
                'receive an empty stream from the client! '
                'please check your client\'s inputs, '
                'you can use "Client.check_input(inputs)"'
            )
            return

        # the total num requests < self.args.prefetch
        if is_req_empty:
            for r in asyncio.as_completed(prefetch_task):
                yield await r
        else:
            # if there are left over (`else` clause above is unnecessary for code but for better readability)
            onrecv_task = []
            # the following code "interleaves" prefetch_task and onrecv_task, when one dries, it switches to the other
            while prefetch_task:
                if self.logger.debug_enabled:
                    self.logger.debug(
                        f'send: {self.iolet.msg_sent} '
                        f'recv: {self.iolet.msg_recv} '
                        f'pending: {self.iolet.msg_sent - self.iolet.msg_recv}'
                    )
                onrecv_task.clear()
                for r in asyncio.as_completed(prefetch_task):
                    yield await r
                    if not is_req_empty:
                        is_req_empty = await prefetch_req(
                            self.args.prefetch_on_recv, onrecv_task
                        )

                # this list dries, clear it and feed it with on_recv_task
                prefetch_task.clear()
                prefetch_task = [j for j in onrecv_task]
