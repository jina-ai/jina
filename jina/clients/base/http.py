from typing import Callable, Dict, Optional
from contextlib import nullcontext, AsyncExitStack

from ..base import BaseClient, InputType
from ..helper import callback_exec
from ...excepts import BadClient
from ...importer import ImportExtensions
from ...logging.profile import ProgressBar
from ...types.request import Request
from ...peapods.runtimes.prefetch.client import HTTPClientPrefetcher


class HTTPClientlet:
    """HTTP Client to be used with prefetcher"""

    def __init__(self, url: str) -> None:
        """HTTP Client to be used with prefetcher

        :param url: url to send POST request to
        """
        self.url = url
        self.msg_recv = 0
        self.msg_sent = 0
        self.session = None

    async def send_message(self, request: Dict):
        """Sends a POST request to the server

        :param request: request as dict
        :return: send post message
        """
        return await self.session.post(url=self.url, json=request).__aenter__()

    async def __aenter__(self):
        """enter async context

        :return: start self
        """
        return await self.start()

    async def start(self):
        """Create ClientSession and enter context

        :return: self
        """
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


class HTTPBaseClient(BaseClient):
    """A MixIn for HTTP Client."""

    async def _get_results(
        self,
        inputs: InputType,
        on_done: Callable,
        on_error: Optional[Callable] = None,
        on_always: Optional[Callable] = None,
        **kwargs,
    ):
        """
        :param inputs: the callable
        :param on_done: the callback for on_done
        :param on_error: the callback for on_error
        :param on_always: the callback for on_always
        :param kwargs: kwargs for _get_task_name and _get_requests
        :yields: generator over results
        """
        with ImportExtensions(required=True):
            import aiohttp

        self.inputs = inputs
        request_iterator = self._get_requests(**kwargs)

        async with AsyncExitStack() as stack:
            try:
                cm1 = ProgressBar() if self.show_progress else nullcontext()
                proto = 'https' if self.args.https else 'http'
                url = f'{proto}://{self.args.host}:{self.args.port}/post'

                p_bar = stack.enter_context(cm1)
                iolet = await stack.enter_async_context(HTTPClientlet(url=url))

                prefetcher = HTTPClientPrefetcher(self.args, iolet=iolet)
                async for response in prefetcher.send(request_iterator):
                    r_status = response.status
                    r_str = await response.json()
                    if r_status == 404:
                        raise BadClient(f'no such endpoint {url}')
                    elif r_status < 200 or r_status > 300:
                        raise ValueError(r_str)

                    resp = Request(r_str)
                    resp = resp.as_typed_request(resp.request_type).as_response()
                    callback_exec(
                        response=resp,
                        on_error=on_error,
                        on_done=on_done,
                        on_always=on_always,
                        continue_on_error=self.continue_on_error,
                        logger=self.logger,
                    )
                    if self.show_progress:
                        p_bar.update()
                    yield resp
            except aiohttp.client_exceptions.ClientConnectorError:
                self.logger.warning(f'Client got disconnected from the HTTP server')
