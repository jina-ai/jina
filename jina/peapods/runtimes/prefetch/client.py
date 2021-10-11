import asyncio
from typing import TYPE_CHECKING

from .base import BasePrefetcher

__all__ = ['HTTPClientPrefetcher', 'WebsocketClientPrefetcher']

if TYPE_CHECKING:
    from ....types.request import Request


class ClientPrefetcher(BasePrefetcher):
    """Client Prefetcher to be inherited by HTTP / Websocket Prefetchers"""

    def convert_to_message(self, request):
        return request


class HTTPClientPrefetcher(ClientPrefetcher):
    """An async HTTP request handler used in the HTTP Client"""

    async def receive(self):
        """For HTTP Client, there's no task needed for receiving.
        Sleep like there's no tomorrow!

        :return: asyncio Task
        """
        return await asyncio.sleep(1e9)

    def handle_request(self, request: 'Request') -> 'asyncio.Task':
        """
        For HTTP Client, for each request in the iterator, we `send_message` using
        http POST request and add it to the list of tasks which is awaited and yielded.

        :param request: current request in the iterator
        :return: asyncio Task for sending message
        """
        return asyncio.create_task(self.iolet.send_message(request=request))

    def handle_response(self):
        """No responses to handle for HTTP Client"""
        pass

    def handle_end_of_iter(self):
        """Iterator end doesn't need to be managed for HTTP Client"""
        pass


class WebsocketClientPrefetcher(ClientPrefetcher):
    """An async request/response handler used in the Websocket Client"""

    async def receive(self):
        """Await messages from Gateway and process them in the request buffer"""
        try:
            async for response in self.iolet.recv_message():
                self.handle_response(response)
        finally:
            if self.request_buffer:
                self.logger.warning(
                    f'{self.__class__.__name__} closed, cancelling all outstanding requests'
                )
                for future in self.request_buffer.values():
                    future.cancel()
                self.request_buffer.clear()

    def handle_end_of_iter(self):
        """Send End of iteration signal to the Gateway"""
        asyncio.create_task(self.iolet.send_eoi())
