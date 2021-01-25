import asyncio
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, WebSocket
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from starlette.endpoints import WebSocketEndpoint
from starlette.types import Receive, Scope, Send

from ... import daemon_logger, jinad_args
from ...stores.helper import get_workspace_path

router = APIRouter(tags=['logs'])


@router.get(
    path='/logs/{workspace_id}/{log_id}'
)
async def _export_logs(
        workspace_id: uuid.UUID,
        log_id: uuid.UUID
):
    filepath = get_workspace_path(workspace_id, log_id, 'logging.log')
    if not Path(filepath).is_file():
        raise HTTPException(status_code=404, detail=f'log file {log_id} not found in workspace {workspace_id}')
    else:
        return FileResponse(filepath)


class LogStreamingEndpoint(WebSocketEndpoint):

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        super().__init__(scope, receive, send)
        # Accessing path / query params from scope in ASGI
        # https://asgi.readthedocs.io/en/latest/specs/www.html#websocket-connection-scope
        info = self.scope.get('path').split('/')
        workspace_id = info[-2]
        log_id = info[-1]
        self.filepath = get_workspace_path(workspace_id, log_id, 'logging.log')
        self.active_clients = []

    async def on_connect(self, websocket: WebSocket) -> None:
        await websocket.accept()

        self.client_details = f'{websocket.client.host}:{websocket.client.port}'
        self.active_clients.append(websocket)
        daemon_logger.info(f'{self.client_details} is connected to stream logs!')

        if jinad_args.no_fluentd:
            daemon_logger.warning(f'{self.client_details} asks for logstreaming but fluentd is not available')
            return

        # on connection the fluentd file may not flushed (aka exist) yet
        while not Path(self.filepath).is_file():
            daemon_logger.info(f'still waiting {self.filepath} to be ready...')
            await asyncio.sleep(1)

        with open(self.filepath) as fp:
            fp.seek(0, 2)
            daemon_logger.success(f'{self.filepath} is ready for streaming')
            while websocket in self.active_clients:
                line = fp.readline()  # also possible to read an empty line
                if line:
                    payload = None
                    try:
                        payload = json.loads(line)
                    except json.decoder.JSONDecodeError:
                        daemon_logger.warning(f'JSON decode error on {line}')

                    if payload:
                        from websockets import ConnectionClosedOK
                        try:
                            await websocket.send_json(payload)
                        except ConnectionClosedOK:
                            break
                else:
                    await asyncio.sleep(0.1)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        self.active_clients.remove(websocket)
        daemon_logger.info(f'{self.client_details} is disconnected')


# TODO: adding websocket in this way do not generate any docs
#  see: https://github.com/tiangolo/fastapi/issues/1983
router.add_websocket_route(path='/logstream/{workspace_id}/{log_id}',
                           endpoint=LogStreamingEndpoint)
