import asyncio
import json
import uuid
from pathlib import Path
from typing import List

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


class ConnectionManager:
    """
    Manager of websockets listening for a log stream.

    TODO for now contian a single connection. Ideally there must be one
    manager per log with a thread checking for updates in log and broadcasting
    to active connections
    """

    def __init__(self):
        """Instantiate a ConnectionManager."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Register a new websocket.

        :param websocket: websocket to register
        """
        await websocket.accept()
        daemon_logger.info(
            '%s is connected to stream logs!' % _websocket_details(websocket)
        )
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        """
        Disconnect a websocket.

        :param websocket: websocket to disconnect
        """
        self.active_connections.remove(websocket)
        await websocket.close()
        daemon_logger.info('%s is disconnected' % _websocket_details(websocket))

    async def broadcast(self, message: dict):
        """
        Send a json message to all registered websockets.

        :param message: JSON-serializable message to be broadcast
        """
        daemon_logger.debug('connections: %r', self.active_connections)
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except ConnectionClosedOK:
                pass
            except ConnectionClosedError:
                await self.disconnect(connection)


@router.websocket('/logstream/{workspace_id}/{log_id}')
async def _logstream(
    websocket: WebSocket, workspace_id: uuid.UUID, log_id: uuid.UUID, timeout: int = 0
):
    manager = ConnectionManager()
    await manager.connect(websocket)
    client_details = _websocket_details(websocket)
    filepath = get_workspace_path(workspace_id, log_id, 'logging.log')
    try:
        if jinad_args.no_fluentd:
            daemon_logger.warning(
                f'{client_details} asks for logstreaming but fluentd is not available'
            )
            return

        # on connection the fluentd file may not flushed (aka exist) yet
        n = 0
        while not Path(filepath).is_file():
            daemon_logger.debug(f'still waiting {filepath} to be ready...')
            await asyncio.sleep(1)
            n += 1
            if timeout > 0 and n >= timeout:
                return

        daemon_logger.success(f'{filepath} is ready for streaming')

        with open(filepath) as fp:
            fp.seek(0, 2)
            delay = 0.1
            n = 0
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
                        n = 0
                else:
                    await asyncio.sleep(delay)
                    n += 1
                    if timeout > 0 and n >= timeout / delay:
                        return
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    finally:
        await manager.disconnect(websocket)
