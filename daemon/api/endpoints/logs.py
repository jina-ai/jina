import asyncio
from pathlib import Path
from typing import Any

from fastapi import APIRouter, WebSocket
from starlette.endpoints import WebSocketEndpoint
from starlette.types import Receive, Scope, Send

from ... import daemon_logger, jinad_args

router = APIRouter()


class LogStreamingEndpoint(WebSocketEndpoint):

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        super().__init__(scope, receive, send)

        # Accessing path / query params from scope in ASGI
        # https://asgi.readthedocs.io/en/latest/specs/www.html#websocket-connection-scope
        self.log_id = self.scope.get('path').split('/')[-1]
        self.filepath = jinad_args.log_path % self.log_id
        self.active_clients = []

    async def on_connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        # FastAPI & Starlette still don't have a generic WebSocketException
        # https://github.com/encode/starlette/pull/527
        # The following `raise` raises `websockets.exceptions.ConnectionClosedError` (code = 1006)
        # TODO(Deepankar): This needs better handling.
        if not Path(self.filepath).is_file():
            raise FileNotFoundError(f'File {self.filepath} not found locally')

        self.active_clients.append(websocket)
        self.client_details = f'{websocket.client.host}:{websocket.client.port}'
        daemon_logger.info(f'Client {self.client_details} got connected to stream Fluentd logs!')

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        if not Path(self.filepath).is_file():
            raise FileNotFoundError(f'File {self.filepath} not found locally')

        with open(self.filepath) as fp:
            fp.seek(0, 2)
            while True:
                readline = fp.readline()
                line = readline.strip()
                if line:
                    await websocket.send_json(line)
                else:
                    await asyncio.sleep(0.1)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        self.active_clients.remove(websocket)
        daemon_logger.info(f'Client {self.client_details} got disconnected!')


# TODO: adding websocket in this way do not generate any docs
#  see: https://github.com/tiangolo/fastapi/issues/1983
router.add_websocket_route(path='/logstream/{log_id}',
                           endpoint=LogStreamingEndpoint)
