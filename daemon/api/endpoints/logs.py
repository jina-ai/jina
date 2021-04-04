import asyncio
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from starlette.endpoints import WebSocketEndpoint
from starlette.types import Receive, Scope, Send
from websockets import ConnectionClosedOK
from websockets.exceptions import ConnectionClosedError

from ... import daemon_logger, jinad_args
from ...stores.helper import get_workspace_path

router = APIRouter(tags=['logs'])


def _log_is_ready(workspace_id: uuid.UUID, log_id: uuid.UUID):
    filepath = get_workspace_path(workspace_id, log_id, 'logging.log')
    return Path(filepath).is_file()


@router.get(path='/logs/{workspace_id}/{log_id}')
async def _export_logs(workspace_id: uuid.UUID, log_id: uuid.UUID):
    filepath = get_workspace_path(workspace_id, log_id, 'logging.log')
    if not Path(filepath).is_file():
        raise HTTPException(
            status_code=404,
            detail=f'log file {log_id} not found in workspace {workspace_id}',
        )
    else:
        return FileResponse(filepath)


def _websocket_details(websocket: WebSocket):
    return f'{websocket.client.host}:{websocket.client.port}'


# cf https://fastapi.tiangolo.com/advanced/websockets/
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        daemon_logger.info(
            '%s is connected to stream logs!' % _websocket_details(websocket)
        )
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        websocket.close()
        daemon_logger.info('%s is disconnected' % _websocket_details(websocket))

    async def broadcast(self, message: dict):
        daemon_logger.debug('connections: %r', self.active_connections)
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except ConnectionClosedOK:
                pass
            except ConnectionClosedError:
                self.active_connections.remove(connection)


manager = ConnectionManager()


@router.websocket("/logstream/{workspace_id}/{log_id}")
async def _logstream(websocket: WebSocket, workspace_id: uuid.UUID, log_id: uuid.UUID):
    await manager.connect(websocket)
    filepath = get_workspace_path(workspace_id, log_id, 'logging.log')
    try:
        if jinad_args.no_fluentd:
            daemon_logger.warning(
                f'{self.client_details} asks for logstreaming but fluentd is not available'
            )
            manager.disconnect(websocket)
            return

        # on connection the fluentd file may not flushed (aka exist) yet
        while not Path(filepath).is_file():
            daemon_logger.debug(f'still waiting {filepath} to be ready...')
            await asyncio.sleep(1)

        daemon_logger.success(f'{filepath} is ready for streaming')

        with open(filepath) as fp:
            fp.seek(0, 2)
            while True:
                line = fp.readline()  # also possible to read an empty line
                if line:
                    daemon_logger.debug('sending line %s', line)
                    payload = None
                    try:
                        payload = json.loads(line)
                    except json.decoder.JSONDecodeError:
                        daemon_logger.warning(f'JSON decode error on {line}')

                    if payload:
                        await manager.broadcast(payload)
                else:
                    await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
