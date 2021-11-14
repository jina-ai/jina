"""A module for the websockets-based Client for Jina."""
from contextlib import nullcontext, AsyncExitStack
from typing import Optional, TYPE_CHECKING

from .helper import WebsocketClientlet
from ..base import BaseClient
from ..helper import callback_exec
from ...importer import ImportExtensions
from ...logging.profile import ProgressBar
from ...peapods.stream.client import WebsocketClientStreamer

if TYPE_CHECKING:
    from ..base import CallbackFnType, InputType


class WebSocketBaseClient(BaseClient):
    """A Websocket Client."""

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

                proto = 'wss' if self.args.https else 'ws'
                url = f'{proto}://{self.args.host}:{self.args.port}/'
                iolet = await stack.enter_async_context(
                    WebsocketClientlet(url=url, logger=self.logger)
                )

                streamer = WebsocketClientStreamer(self.args, iolet=iolet)
                async for response in streamer.stream(request_iterator):
                    callback_exec(
                        response=response,
                        on_error=on_error,
                        on_done=on_done,
                        on_always=on_always,
                        continue_on_error=self.continue_on_error,
                        logger=self.logger,
                    )
                    if self.show_progress:
                        p_bar.update()
                    yield response

            except aiohttp.ClientError as e:
                self.logger.error(
                    f'Error while streaming response from websocket server {e!r}'
                )
