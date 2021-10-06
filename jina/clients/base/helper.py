import asyncio
from typing import TYPE_CHECKING, Optional
from abc import ABC, abstractmethod

from ...types.request import Request
from ...importer import ImportExtensions

if TYPE_CHECKING:
    from ...types.request import Response


class AioHttpClientlet(ABC):
    """aiohttp session manager"""

    def __init__(self, url: str) -> None:
        """HTTP Client to be used with prefetcher

        :param url: url to send POST request to
        """
        self.url = url
        self.msg_recv = 0
        self.msg_sent = 0
        self.session = None

    @abstractmethod
    async def send_message(self):
        """Send message to Gateway"""
        ...

    @abstractmethod
    async def recv_message(self):
        """Receive message from Gateway"""
        ...

    async def __aenter__(self):
        """enter async context

        :return: start self
        """
        return await self.start()

    async def start(self):
        """Create ClientSession and enter context

        :return: self
        """
        with ImportExtensions(required=True):
            import aiohttp

        self.session = aiohttp.ClientSession()
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close(exc_type, exc_val, exc_tb)

    async def close(self, *args, **kwargs):
        """Close ClientSession

        :param args: positional args
        :param kwargs: keyword args"""
        await self.session.__aexit__(*args, **kwargs)


class HTTPClientlet(AioHttpClientlet):
    """HTTP Client to be used with prefetcher"""

    async def send_message(self, request: 'Request'):
        """Sends a POST request to the server

        :param request: request as dict
        :return: send post message
        """
        req_dict = request.dict()
        req_dict['exec_endpoint'] = req_dict['header']['exec_endpoint']
        req_dict['data'] = req_dict['data'].get('docs', None)
        return await self.session.post(url=self.url, json=req_dict).__aenter__()

    async def recv_message(self):
        """Receive message for HTTP (sleep)

        :return: await sleep
        """
        return await asyncio.sleep(1e10)


class WebsocketClientlet(AioHttpClientlet):
    """Websocket Client to be used with prefetcher"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ws = None

    async def send_message(self, request: Optional['Request'] = None):
        """Send request in bytes to the server

        :param request: request object
        :return: send bytes awaitable
        """
        return await self.ws.send_bytes(
            request.SerializeToString() if request else bytes(True)
        )

    async def recv_message(self) -> 'Response':
        """Receive messages in bytes from server and convert to `Response`

        :return: response object from bytes
        """
        from aiohttp import WSMsgType

        async for response in self.ws:
            print(f'\n\n\nrecv_message called, self._waiting: {self.ws._waiting}\n\n\n')
            if response.type == WSMsgType.CLOSE:
                print('CLOSE')
                break
            else:
                response_bytes = response.data
                print(f'\n\n\ngot a response {response_bytes}\n\n')
                resp = Request(response_bytes)
                return resp.as_typed_request(resp.request_type).as_response()

    async def __aenter__(self):
        await super().__aenter__()
        self.ws = await self.session.ws_connect(url=self.url).__aenter__()
        return self
