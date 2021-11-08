import argparse

from typing import TYPE_CHECKING, AsyncIterator

from .base import BaseStreamer
from ...types.message import Message

__all__ = ['ZmqGatewayStreamer', 'GrpcGatewayStreamer']

if TYPE_CHECKING:
    from ..grpc import Grpclet
    from ...types.request import Request, Response


class GatewayStreamer(BaseStreamer):
    """Streamer used at Gateway to stream requests/responses to/from Executors"""

    def _convert_to_message(self, request: 'Request') -> Message:
        """Convert `Request` to `Message`

        :param request: current request in the iterator
        :return: Message object
        """
        return Message(None, request, 'gateway', **vars(self.args))

    async def stream(self, request_iterator, *args) -> AsyncIterator['Request']:
        """
        stream requests from client iterator and stream responses back.

        :param request_iterator: iterator of requests
        :param args: positional arguments
        :yield: responses from Executors
        """
        if self.receive_task.done():
            raise RuntimeError('receive task not running, can not send messages')

        async_iter: AsyncIterator = (
            self._stream_requests_with_prefetch(request_iterator, self.args.prefetch)
            if self.args.prefetch > 0
            else self._stream_requests(request_iterator)
        )

        async for response in async_iter:
            yield response

    # alias of stream used as a grpc servicer
    Call = stream


class ZmqGatewayStreamer(GatewayStreamer):
    """Streamer used at Gateway to stream ZMQ requests/responses to/from Executors"""

    async def _receive(self):
        """Await messages back from Executors and process them in the request buffer"""
        try:
            while True:
                response = await self.iolet.recv_message(callback=lambda x: x.response)
                # during shutdown the socket will return None
                if response is None:
                    break

                self._handle_response(response)
        finally:
            if self.request_buffer:
                self.logger.warning(
                    f'{self.__class__.__name__} closed, cancelling all outstanding requests'
                )
                for future in self.request_buffer.values():
                    future.cancel()
                self.request_buffer.clear()


class GrpcGatewayStreamer(GatewayStreamer):
    """Streamer used at Gateway to stream GRPC requests/responses to/from Executors"""

    def __init__(self, args: argparse.Namespace, iolet: 'Grpclet'):
        super().__init__(args, iolet)
        self.iolet.callback = lambda response: self._handle_response(response.request)

    async def _receive(self):
        """Start grpclet and await termination

        :return: await iolet start
        """
        return await self.iolet.start()

    async def _handle_response(self, response: 'Response'):
        """
        Async version of parents handle_response function

        :param response: message received from grpclet callback
        """
        super()._handle_response(response)
