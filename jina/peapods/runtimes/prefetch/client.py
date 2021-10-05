import asyncio
from typing import List, TYPE_CHECKING

from .base import BasePrefetcher
from ....helper import get_or_reuse_loop

__all__ = ['HTTPClientPrefetcher', 'WebsocketPrefetcher']

if TYPE_CHECKING:
    from ....types.request import Request


class ClientPrefetcher(BasePrefetcher):
    """Client Prefetcher to be inherited by HTTP / Websocket Prefetchers"""


class HTTPClientPrefetcher(ClientPrefetcher):
    """An async HTTP request handler used in the HTTP Client"""

    def _create_receive_task(self) -> 'asyncio.Task':
        """Create receive task

        :return: asyncio Task
        """
        return get_or_reuse_loop().create_task(self.receive())

    async def receive(self):
        """
        For HTTP Client, there's no task needed for receiving.
        Sleep like there's no tomorrow!
        """
        await asyncio.sleep(1e9)

    def convert_to_message(self, request: 'Request', **kwargs):
        """Convert request to dict for POST request

        :param request: request from client
        :param kwargs: keyword args
        :return: request as dict
        """
        req_dict = request.dict()
        req_dict['exec_endpoint'] = req_dict['header']['exec_endpoint']
        req_dict['data'] = req_dict['data'].get('docs', None)
        return req_dict

    def handle_request(self, request: 'Request') -> 'asyncio.Task':
        """
        For HTTP Client, for each request in the iterator, we send the message (http POST request)
        and add it to the list of tasks which is awaited.

        :param request: current request in the iterator
        :return: asyncio Task for sending message
        """
        return asyncio.create_task(
            self.iolet.send_message(self.convert_to_message(request=request))
        )


class WebsocketPrefetcher(ClientPrefetcher):
    """An async request/response handler used in the Websocket Client (tbd)"""
