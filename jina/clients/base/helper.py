import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from aiohttp import WSMsgType

from jina.enums import WebsocketSubProtocols
from jina.importer import ImportExtensions
from jina.types.request import Request
from jina.types.request.data import DataRequest
from jina.types.request.status import StatusMessage

if TYPE_CHECKING:
    from jina.logging.logger import JinaLogger


class AioHttpClientlet(ABC):
    """aiohttp session manager"""

    def __init__(self, url: str, logger: 'JinaLogger', **kwargs) -> None:
        """HTTP Client to be used with the streamer

        :param url: url to send http/websocket request to
        :param logger: jina logger
        :param kwargs: kwargs  which will be forwarded to the `aiohttp.Session` instance. Used to pass headers to requests
        """
        self.url = url
        self.logger = logger
        self.msg_recv = 0
        self.msg_sent = 0
        self.session = None
        self._session_kwargs = {}
        if kwargs.get('headers', None):
            self._session_kwargs['headers'] = kwargs.get('headers')
        if kwargs.get('auth', None):
            self._session_kwargs['auth'] = kwargs.get('auth')
        if kwargs.get('cookies', None):
            self._session_kwargs['cookies'] = kwargs.get('cookies')

    @abstractmethod
    async def send_message(self, **kwargs):
        """Send message to Gateway
        :param kwargs: kwargs which will be forwarded to the `aiohttp.Session.post` method. Used to pass headers to requests
        """
        ...

    @abstractmethod
    async def send_dry_run(self, **kwargs):
        """Query the dry_run endpoint from Gateway
        :param kwargs: kwargs which will be forwarded to the `aiohttp.Session.post` method. Used to pass headers to requests
        """
        ...

    @abstractmethod
    async def recv_message(self):
        """Receive message from Gateway"""
        ...

    async def recv_dry_run(self):
        """Receive dry run response from Gateway"""
        pass

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

        self.session = aiohttp.ClientSession(**self._session_kwargs)
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
    """HTTP Client to be used with the streamer"""

    async def send_message(self, request: 'Request'):
        """Sends a POST request to the server

        :param request: request as dict
        :return: send post message
        """
        req_dict = request.to_dict()
        req_dict['exec_endpoint'] = req_dict['header']['exec_endpoint']
        if 'target_executor' in req_dict['header']:
            req_dict['target_executor'] = req_dict['header']['target_executor']
        return await self.session.post(url=self.url, json=req_dict).__aenter__()

    async def send_dry_run(self):
        """Query the dry_run endpoint from Gateway
        :return: send get message
        """
        return await self.session.get(url=self.url).__aenter__()

    async def recv_message(self):
        """Receive message for HTTP (sleep)

        :return: await sleep
        """
        return await asyncio.sleep(1e10)

    async def recv_dry_run(self):
        """Receive dry run response for HTTP (sleep)

        :return: await sleep
        """
        return await asyncio.sleep(1e10)


class WsResponseIter:
    """
    Iterates over all the responses that come in over the websocket connection.
    In contrast to the iterator built into AioHTTP, this also records the message that was sent at closing-time.
    """

    def __init__(self, websocket):
        self.websocket = websocket
        self.close_message = None

    def __aiter__(self):
        return self

    async def __anext__(self):
        msg = await self.websocket.receive()
        if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.CLOSED):
            self.close_message = msg
            raise StopAsyncIteration
        return msg


class WebsocketClientlet(AioHttpClientlet):
    """Websocket Client to be used with the streamer"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.websocket = None
        self.response_iter = None

    async def send_message(self, request: 'Request'):
        """Send request in bytes to the server.

        :param request: request object
        :return: send request as bytes awaitable
        """
        try:
            return await self.websocket.send_bytes(request.SerializeToString())
        except ConnectionResetError:
            self.logger.critical(f'server connection closed already!')

    async def send_dry_run(self):
        """Query the dry_run endpoint from Gateway

        :return: send dry_run as bytes awaitable
        """

        try:
            return await self.websocket.send_bytes(b'')
        except ConnectionResetError:
            self.logger.critical(f'server connection closed already!')

    async def send_eoi(self):
        """To confirm end of iteration, we send `bytes(True)` to the server.

        :return: send `bytes(True)` awaitable
        """
        try:
            return await self.websocket.send_bytes(bytes(True))
        except ConnectionResetError:
            # server might be in a `CLOSING` state while sending EOI signal
            # which raises a `ConnectionResetError`, this can be ignored.
            pass

    async def recv_message(self) -> 'DataRequest':
        """Receive messages in bytes from server and convert to `DataRequest`

        ..note::
            aiohttp allows only one task which can `receive` concurrently.
            we need to make sure we don't create multiple tasks with `recv_message`

        :yield: response objects received from server
        """
        async for response in self.response_iter:
            yield DataRequest(response.data)

    async def recv_dry_run(self):
        """Receive dry run response in bytes from server

        ..note::
            aiohttp allows only one task which can `receive` concurrently.
            we need to make sure we don't create multiple tasks with `recv_message`

        :yield: response objects received from server
        """
        async for response in self.response_iter:
            yield StatusMessage(response.data)

    async def __aenter__(self):
        await super().__aenter__()
        self.websocket = await self.session.ws_connect(
            url=self.url,
            protocols=(WebsocketSubProtocols.BYTES.value,),
            **self._session_kwargs,
        ).__aenter__()
        self.response_iter = WsResponseIter(self.websocket)
        return self

    @property
    def close_message(self):
        """:return: the close message (reason) of the ws closing response"""
        return self.response_iter.close_message.extra if self.response_iter else None

    @property
    def close_code(self):
        """:return: the close code of the ws closing response"""
        return self.websocket.close_code if self.websocket else None
