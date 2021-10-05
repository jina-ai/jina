import argparse
import asyncio
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Union, TYPE_CHECKING

from ...grpc import Grpclet
from ....helper import typename
from ....logging.logger import JinaLogger
from ....types.message import Message

__all__ = ['BasePrefetcher']

if TYPE_CHECKING:
    from ...zmq import AsyncZmqlet
    from ....types.request import Request
    from ....clients.base.http import HTTPClientlet


class BasePrefetcher(ABC):
    """An base async request/response handler"""

    def __init__(
        self,
        args: argparse.Namespace,
        iolet: Union['AsyncZmqlet', 'Grpclet', 'HTTPClientlet'],
    ):
        """
        :param args: args from CLI
        :param iolet: One of AsyncZmqlet or Grpclet. Used for sending/receiving data to/from the Flow
        """
        self.args = args
        self.iolet = iolet
        self.receive_task = self._create_receive_task()
        self.logger = JinaLogger(self.__class__.__name__, **vars(args))

    @abstractmethod
    def _create_receive_task(self) -> asyncio.Task:
        """Start a receive task to be running in the background

        .. # noqa: DAR202
        :return: asyncio Task
        """
        ...

    @abstractmethod
    async def receive(self):
        """Implement `receive` logic for prefetcher

        .. # noqa: DAR202
        """
        ...

    @abstractmethod
    def handle_request(
        self, request: 'Request'
    ) -> Union['asyncio.Task', 'asyncio.Future']:
        """Handle each request in the iterator

        :param request: current request in the iterator
        """
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
        self.args: argparse.Namespace
        self.iolet: Union['AsyncZmqlet', 'Grpclet']
        self.logger: JinaLogger

        if self.receive_task.done():
            raise RuntimeError(
                'PrefetchCaller receive task not running, can not send messages'
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
