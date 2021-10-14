import asyncio
from typing import TYPE_CHECKING, AsyncIterator, Awaitable

from .base import BaseStreamer

__all__ = ['HTTPClientStreamer', 'WebsocketClientStreamer']

if TYPE_CHECKING:
    from ...types.request import Request


class ClientStreamer(BaseStreamer):
    """Streamer used at Client to stream requests/responses to/from Gateway"""

    def _convert_to_message(self, request):
        return request

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


class HTTPClientStreamer(ClientStreamer):
    """Streamer used at Client to stream HTTP requests/responses to/from HTTPGateway"""

    async def _receive(self) -> Awaitable:
        """For HTTP Client, there's no task needed for receiving.
        Sleep like there's no tomorrow!

        :return: awaitable
        """
        return await asyncio.sleep(1e9)

    def _handle_request(self, request: 'Request') -> 'asyncio.Future':
        """
        For HTTP Client, for each request in the iterator, we `send_message` using
        http POST request and add it to the list of tasks which is awaited and yielded.

        :param request: current request in the iterator
        :return: asyncio Task for sending message
        """
        return asyncio.ensure_future(self.iolet.send_message(request=request))

    def _handle_response(self):
        """No responses to handle for HTTP Client"""
        pass


class WebsocketClientStreamer(ClientStreamer):
    """Streamer used at Client to stream Websocket requests/responses to/from WebsocketGateway"""

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

    def _handle_end_of_iter(self):
        """Send End of iteration signal to the Gateway"""
        asyncio.create_task(self.iolet.send_eoi())
