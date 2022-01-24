import asyncio
import json
from pathlib import Path
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from starlette.websockets import WebSocketState
from websockets import ConnectionClosedOK
from websockets.exceptions import ConnectionClosedError

from daemon import daemon_logger, jinad_args
from daemon.helper import get_log_file_path
from daemon.models import DaemonID
from daemon.stores import get_store_from_id

router = APIRouter(tags=['logs'])


@router.get(path='/logs/{log_id}')
async def _export_logs(log_id: DaemonID):
    try:
        filepath, workspace_id = get_log_file_path(log_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f'log file {log_id} not found in {get_store_from_id(log_id)._kind} store',
        )
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
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket.application_state != WebSocketState.DISCONNECTED:
            await websocket.close()
            daemon_logger.info('%s is disconnected' % _websocket_details(websocket))

    async def broadcast(self, message: dict):
        """
        Send a json message to all registered websockets.

        :param message: JSON-serializable message to be broadcast
        """
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except ConnectionClosedOK:
                await self.disconnect(connection)
            except ConnectionClosedError:
                await self.disconnect(connection)

    def _has_active_connections(self):
        return any(
            connection.application_state != WebSocketState.DISCONNECTED
            for connection in self.active_connections
        )
