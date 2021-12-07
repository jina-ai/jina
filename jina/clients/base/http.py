from contextlib import nullcontext, AsyncExitStack
from typing import Optional, TYPE_CHECKING

from .helper import HTTPClientlet
from ..base import BaseClient
from ..helper import callback_exec
from ...excepts import BadClient
from ...importer import ImportExtensions
from ...logging.profile import ProgressBar
from ...peapods.stream.client import HTTPClientStreamer
from ...types.request import Request

if TYPE_CHECKING:
    from ..base import InputType, CallbackFnType


class HTTPBaseClient(BaseClient):
    """A MixIn for HTTP Client."""

    async def _get_results(
        self,
        inputs: 'InputType',
        on_done: 'CallbackFnType',
        on_error: Optional['CallbackFnType'] = None,
        on_always: Optional['CallbackFnType'] = None,
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
                cm1 = (
                    ProgressBar(total_length=self._inputs_length)
                    if self.show_progress
                    else nullcontext()
                )
                p_bar = stack.enter_context(cm1)

                proto = 'https' if self.args.https else 'http'
                url = f'{proto}://{self.args.host}:{self.args.port}/post'
                iolet = await stack.enter_async_context(
                    HTTPClientlet(url=url, logger=self.logger)
                )

                streamer = HTTPClientStreamer(self.args, iolet=iolet)
                async for response in streamer.stream(request_iterator):
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
            except aiohttp.ClientError as e:
                self.logger.error(
                    f'Error while fetching response from HTTP server {e!r}'
                )
