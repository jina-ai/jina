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

    def convert_to_message(self, request: 'Request'):
        """Convert a `Request` to a `Message` to be sent from gateway

        :param request: request from iterator
        :return: Message from request
        """
        return Message(None, request, 'gateway', **vars(self.args))

    def handle_request(self, request: 'Request') -> 'asyncio.Future':
        """
        For ZMQ & GRPC data requests, for each request in the iterator, we send the `Message` using
        `iolet.send_message()` and add {<request-id>: <an-empty-future>} to the message buffer.
        This empty future is used to track the `result` of this request during `receive`

        :param request: current request in the iterator
        :return: asyncio Future for sending message
        """
        future = get_or_reuse_loop().create_future()
        self.request_buffer[request.request_id] = future
        asyncio.create_task(
            self.iolet.send_message(self.convert_to_message(request=request))
        )
        return future

    async def receive(self):
        """Await messages back from Executors and process them in the message buffer"""
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
            for future in self.request_buffer.values():
                future.cancel(
                    f'{self.__class__.__name__} closed, all outstanding requests canceled'
                )
            self.request_buffer.clear()

    def handle_response(self, response: 'Response'):
        """
        Set result of each response received from Executors in the request buffer

        :param response: message received during `iolet.recv_message`
        """
        if response.request_id in self.request_buffer:
            future = self.request_buffer.pop(response.request_id)
            future.set_result(response)
        else:
            self.logger.warning(
                f'Discarding unexpected response with request id {response.request_id}'
            )


class ZmqGatewayPrefetcher(GatewayPrefetcher):
    """An async zmq request handler used in the Gateway"""

    def _create_receive_task(self):
        """Start a receive task that starts the GRPC server & awaits termination.

        :return: asyncio Task
        """
        return get_or_reuse_loop().create_task(self.receive())


class GrpcGatewayPrefetcher(GatewayPrefetcher):
    """An async grpc request handler used in the Gateway"""

    def __init__(self, args: argparse.Namespace, iolet: 'Grpclet'):
        super().__init__(args, iolet)
        self.iolet.callback = lambda response: self.handle_response(response.request)

    async def handle_response(self, response: 'Response'):
        """
        Async version of parents handle_response function

        :param response: message received from grpclet callback
        """
        super().handle_response(response)

    def _create_receive_task(self) -> 'asyncio.Task':
        """Start a receive task that starts the GRPC server & awaits termination.

        :return: asyncio Task
        """
        return get_or_reuse_loop().create_task(self.iolet.start())
