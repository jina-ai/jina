import asyncio
import argparse
from abc import ABC, abstractmethod
from typing import (
    Dict,
    Union,
    Awaitable,
    TYPE_CHECKING,
)

from ....helper import get_or_reuse_loop
from ....logging.logger import JinaLogger
from ....types.message import Message

__all__ = ['BaseStreamer']

if TYPE_CHECKING:
    from ...grpc import Grpclet
    from ...zmq import AsyncZmqlet
    from ....types.request import Request, Response
    from ....clients.base.helper import HTTPClientlet, WebsocketClientlet


class BaseStreamer(ABC):
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
        For zmq & grpc data requests from gateway, for each request in the iterator, we send the `Message`
        using `iolet.send_message()`.

        For websocket requests from client, for each request in the iterator, we send the request in `bytes`
        using using `iolet.send_message()`.

        Then add {<request-id>: <an-empty-future>} to the request buffer.
        This empty future is used to track the `result` of this request during `receive`.

        :param request: current request in the iterator
        :return: asyncio Future for sending message
        """
        future = get_or_reuse_loop().create_future()
        self.request_buffer[request.request_id] = future
        asyncio.create_task(self.iolet.send_message(self.convert_to_message(request)))
        return future

    def handle_response(self, response: 'Response') -> None:
        """Set result of each response received in the request buffer

        :param response: response received during `iolet.recv_message`
        """
        if response.request_id in self.request_buffer:
            future = self.request_buffer.pop(response.request_id)
            future.set_result(response)
        else:
            self.logger.warning(
                f'discarding unexpected response with request id {response.request_id}'
            )

    def handle_end_of_iter(self) -> None:
        """Send end of iterator signal to Gateway"""
        pass

    async def close(self):
        """
        Stop receiving messages
        """
        self.receive_task.cancel()
