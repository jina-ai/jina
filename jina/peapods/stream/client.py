import asyncio
from typing import TYPE_CHECKING, AsyncIterator, Dict

from ...helper import get_or_reuse_loop
from .base import BaseStreamer

__all__ = ['HTTPClientStreamer', 'WebsocketClientStreamer']

if TYPE_CHECKING:
    from ...types.request import Request


class ClientStreamer(BaseStreamer):
    """Streamer used at Client to stream requests/responses to/from Gateway"""

    def _convert_to_message(self, request):
        return request


class HTTPClientStreamer(ClientStreamer):
    """Streamer used at Client to stream HTTP requests/responses to/from HTTPGateway"""

    async def stream(self, request_iterator, *args) -> AsyncIterator['Request']:
        """
        Async call to receive Requests and build them into Messages.

        :param request_iterator: iterator of requests.
        :param args: positional args
        :yield: responses
        """
        async for response in self._stream_requests(request_iterator):
            yield response

    def _handle_request(self, request: 'Request') -> 'asyncio.Future':
        """
        For HTTP Client, for each request in the iterator, we `send_message` using
        http POST request and add it to the list of tasks which is awaited and yielded.

        :param request: current request in the iterator
        :return: asyncio Task for sending message
        """
        return asyncio.ensure_future(
            self._connection_pool.send_message(request=request)
        )


class WebsocketClientStreamer(ClientStreamer):
    """Streamer used at Client to stream Websocket requests/responses to/from WebsocketGateway"""

    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.request_buffer: Dict[str, asyncio.Future] = dict()
        self.receive_task = get_or_reuse_loop().create_task(self._receive())

    async def stream(self, request_iterator, *args) -> AsyncIterator['Request']:
        """
        Async call to receive Requests and build them into Messages.

        :param request_iterator: iterator of requests.
        :param args: positional args
        :yield: responses
        """
        if self.receive_task.done():
            raise RuntimeError('receive task not running, can not send messages')

        async for response in self._stream_requests(request_iterator):
            yield response

    async def _receive(self):
        """Await messages from WebsocketGateway and process them in the request buffer"""
        try:
            async for response in self.iolet.recv_message():
                self._handle_response(response)
        finally:
            if self.request_buffer:
                self.logger.warning(
                    f'{self.__class__.__name__} closed, cancelling all outstanding requests'
                )
                for future in self.request_buffer.values():
                    future.cancel()
                self.request_buffer.clear()

    def _handle_request(self, request: 'Request') -> 'asyncio.Future':
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
        asyncio.create_task(
            self._connection_pool.send_message(self._convert_to_message(request))
        )
        return future

    def _handle_response(self, response: 'Response') -> None:
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

    def _handle_end_of_iter(self):
        """Send End of iteration signal to the Gateway"""
        asyncio.create_task(self._connection_pool.send_eoi())
