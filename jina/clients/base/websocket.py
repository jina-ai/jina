"""A module for the websockets-based Client for Jina."""
import asyncio
from contextlib import nullcontext
from typing import Callable, Optional

from ..base import BaseClient, InputType
from ..helper import callback_exec
from ...importer import ImportExtensions
from ...logging.profile import ProgressBar
from ...types.request import Request


class WebSocketBaseClient(BaseClient):
    """A Websocket Client."""

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
            import websockets

        self.inputs = inputs

        req_iter = self._get_requests(**kwargs)
        try:
            # setting `max_size` as None to avoid connection closure due to size of message
            # https://websockets.readthedocs.io/en/stable/api.html?highlight=1009#module-websockets.protocol

            async with websockets.connect(
                f'ws://{self.args.host}:{self.args.port_expose}/',
                max_size=None,
                ping_interval=None,
            ) as websocket:
                # To enable websockets debug logs
                # https://websockets.readthedocs.io/en/stable/cheatsheet.html#debugging
                self.logger.debug(
                    f'connected to {self.args.host}:{self.args.port_expose}'
                )
                self.num_requests = 0
                self.num_responses = 0

                async def _send_requests(request_iterator):
                    next_request = None
                    for next_request in request_iterator:
                        await websocket.send(next_request.SerializeToString())
                        self.num_requests += 1
                    # Check if there was any request generated
                    if next_request is not None:
                        # Server has no way of knowing when to stop the await on sending response back to the client
                        # We send one last message to say `request_iterator` is completed.
                        # On the client side, this :meth:`send` doesn't need to be awaited with a :meth:`recv`
                        await websocket.send(bytes(True))
                    else:
                        # There is nothing to send, disconnect gracefully
                        await websocket.close(reason='No data to send')

                cm1 = ProgressBar() if self.show_progress else nullcontext()

                with cm1 as p_bar:
                    # Unlike gRPC, any arbitrary function (generator) cannot be passed via websockets.
                    # Simply iterating through the `req_iter` makes the request-response sequential.
                    # To make client unblocking, :func:`send_requests` and `recv_responses` are separate tasks

                    asyncio.create_task(_send_requests(request_iterator=req_iter))
                    async for response_bytes in websocket:
                        # When we have a stream of responses, instead of doing `await websocket.recv()`,
                        # we need to traverse through the websocket to recv messages.
                        # https://websockets.readthedocs.io/en/stable/faq.html#why-does-the-server-close-the-connection-after-processing-one-message

                        resp = Request(response_bytes)
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
                        self.num_responses += 1
                        if self.num_requests == self.num_responses:
                            break

        except websockets.exceptions.ConnectionClosedOK:
            self.logger.warning(f'Client got disconnected from the websocket server')
        except websockets.exceptions.WebSocketException as e:
            self.logger.error(
                f'Got following error while streaming requests via websocket: {e!r}'
            )
