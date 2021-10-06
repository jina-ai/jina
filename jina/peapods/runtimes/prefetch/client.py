import asyncio
from typing import List, TYPE_CHECKING

from ....types.request import Request
from jina.types.message.common import ControlMessage
from .base import BasePrefetcher
from ....helper import get_or_reuse_loop

__all__ = ['HTTPClientPrefetcher', 'WebsocketClientPrefetcher']

if TYPE_CHECKING:
    from ....types.request import Request


class ClientPrefetcher(BasePrefetcher):
    """Client Prefetcher to be inherited by HTTP / Websocket Prefetchers"""

    def _create_receive_task(self) -> 'asyncio.Task':
        """For Clients, there's no task needed for receiving.
        Sleep like there's no tomorrow!

        :return: asyncio Task
        """
        return get_or_reuse_loop().create_task(asyncio.sleep(1e9))


class HTTPClientPrefetcher(ClientPrefetcher):
    """An async HTTP request handler used in the HTTP Client"""

    async def receive(self):
        return asyncio.sleep(1e9)

    def handle_request(self, request: 'Request') -> 'asyncio.Task':
        """
        For HTTP Client, for each request in the iterator, we `send_message` using
        http POST request and add it to the list of tasks which is awaited and yielded.

        :param request: current request in the iterator
        :return: asyncio Task for sending message
        """
        return asyncio.create_task(self.iolet.send_message(request=request))

    def handle_end_iter(self):
        return None


class WebsocketClientPrefetcher(ClientPrefetcher):
    """An async request/response handler used in the Websocket Client"""

    async def receive(self):
        return self.iolet.recv_message()

    def handle_request(self, request: 'Request') -> 'asyncio.Task':
        """
        For Websocket Client, for each request in the iterator, we `send_message` using
        bytes and add the `recv_message` task to be awaited & yielded.

        :param request: current request in the iterator
        :return: asyncio Task for receiving message
        """
        return asyncio.create_task(self.iolet.send_message(request=request))
        # return asyncio.create_task(self.iolet.recv_message())

    def handle_end_iter(self):
        # ControlMessage('TERMINATE').request
        return asyncio.create_task(self.iolet.send_message())
        # return asyncio.create_task(self.iolet.recv_message())
