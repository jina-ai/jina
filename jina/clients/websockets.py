from typing import Callable, List

from .base import BaseClient
from .helper import callback_exec
from ..importer import ImportExtensions
from ..logging.profile import TimeContext, ProgressBar
from ..types.request import Request

if False:
    from ..types.request import Response


class WebSocketBaseClient(BaseClient):
    async def _get_results(self,
                           input_fn: Callable,
                           on_done: Callable,
                           on_error: Callable = None,
                           on_always: Callable = None, **kwargs):
        with ImportExtensions(required=True):
            import websockets

        result = []  # type: List['Response']
        self.input_fn = input_fn
        req_iter, tname = self._get_requests(**kwargs)
        try:
            client_info = f'{self.args.host}:{self.args.port_expose}'

            # setting `max_size` as None to avoid connection closure due to size of message
            # https://websockets.readthedocs.io/en/stable/api.html?highlight=1009#module-websockets.protocol
            async with websockets.connect(f'ws://{client_info}/stream', max_size=None) as websocket:
                self.logger.success(f'Connected to the gateway at {client_info}')
                # To enable websockets debug logs
                # https://websockets.readthedocs.io/en/stable/cheatsheet.html#debugging

                with ProgressBar(task_name=tname) as p_bar, TimeContext(tname):
                    # Unlike gRPC, any arbitrary function cannot be passed via websockets.
                    # We'd need to traverse the iterator & convert each request to bytes/string
                    for next_request in req_iter:
                        await websocket.send(next_request.SerializeToString())

                        # When we have a stream of responses, traverse through the websocket to recv messages,
                        # instead of doing `await websocket.recv()`.
                        # https://websockets.readthedocs.io/en/stable/faq.html#why-does-the-server-close-the-connection-after-processing-one-message
                        response_bytes = await websocket.recv()
                        response = Request(response_bytes).to_response()
                        if self.args.return_results:
                            result.append(response)
                        callback_exec(response=response,
                                      on_error=on_error,
                                      on_done=on_done,
                                      on_always=on_always,
                                      continue_on_error=self.args.continue_on_error,
                                      logger=self.logger)
                        p_bar.update(self.args.batch_size)

        except websockets.exceptions.ConnectionClosedOK:
            self.logger.warning(f'Client got disconnected from the websocket server')
        except websockets.exceptions.WebSocketException as e:
            self.logger.error(f'Got following error while streaming requests via websocket: {repr(e)}')
        finally:
            if self.args.return_results:
                return result
