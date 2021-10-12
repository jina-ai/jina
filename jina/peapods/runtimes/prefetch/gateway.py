import asyncio
import argparse

from typing import Dict, List, Union, TYPE_CHECKING

from .base import BasePrefetcher
from ....types.message import Message
from ....helper import get_or_reuse_loop

__all__ = ['ZmqGatewayPrefetcher', 'GrpcGatewayPrefetcher']

if TYPE_CHECKING:
    from ...grpc import Grpclet
    from ...zmq import AsyncZmqlet
    from ....types.request import Request, Response


class GatewayPrefetcher(BasePrefetcher):
    """Gateway Prefetcher to be inherited by ZMQ / GRPC Prefetchers"""

    def __init__(
        self,
        args: argparse.Namespace,
        iolet: Union['AsyncZmqlet', 'Grpclet'],
    ):
        super().__init__(args, iolet)
        self.request_buffer: Dict[str, asyncio.Future[Message]] = dict()
        self.Call = self.send  # Used in grpc servicer

    def convert_to_message(self, request: 'Request') -> Message:
        """Convert `Request` to `Message`

        :param request: current request in the iterator
        :return: Message object
        """
        return Message(None, request, 'gateway', **vars(self.args))

    def handle_end_of_iter(self):
        pass


class ZmqGatewayPrefetcher(GatewayPrefetcher):
    """An async zmq request handler used in the Gateway"""

    async def receive(self):
        """Await messages back from Executors and process them in the request buffer"""
        try:
            while True:
                response = await self.iolet.recv_message(callback=lambda x: x.response)
                # during shutdown the socket will return None
                if response is None:
                    break

                self.handle_response(response)
        except asyncio.CancelledError:
            raise
        finally:
            if self.request_buffer:
                self.logger.warning(
                    f'{self.__class__.__name__} closed, cancelling all outstanding requests'
                )
                for future in self.request_buffer.values():
                    future.cancel()
                self.request_buffer.clear()


class GrpcGatewayPrefetcher(GatewayPrefetcher):
    """An async grpc request handler used in the Gateway"""

    def __init__(self, args: argparse.Namespace, iolet: 'Grpclet'):
        super().__init__(args, iolet)
        self.iolet.callback = lambda response: self.handle_response(response.request)

    async def receive(self):
        """Start grpclet and await termination

        :return: await iolet start
        """
        return await self.iolet.start()

    async def handle_response(self, response: 'Response'):
        """
        Async version of parents handle_response function

        :param response: message received from grpclet callback
        """
        super().handle_response(response)
