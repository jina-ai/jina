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
from ...helper import get_workspace_path
from ...models import DaemonID
from ...models.enums import IDLiterals
from ...stores import get_store_from_id

router = APIRouter(tags=['logs'])


@router.get(path='/logs/log_id}')
async def _export_logs(log_id: DaemonID):
    filepath, workspace_id = _get_log_file_path(log_id)
    if not Path(filepath).is_file():
        raise HTTPException(
            status_code=404,
            detail=f'log file {log_id} not found in workspace {workspace_id}',
        )
    else:
        return FileResponse(filepath)


def _get_log_file_path(log_id):
    if IDLiterals.JWORKSPACE == log_id.jtype:
        workspace_id = log_id
        filepath = get_workspace_path(log_id, 'logs', 'logging.log')
    else:
        workspace_id = get_store_from_id(log_id)[log_id].workspace_id
        filepath = get_workspace_path(workspace_id, 'logs', log_id, 'logging.log')
    return filepath, workspace_id


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


@router.websocket('/logstream/{log_id}')
async def _logstream(websocket: WebSocket, log_id: DaemonID, timeout: int = 0):
    manager = ConnectionManager()
    await manager.connect(websocket)
    client_details = _websocket_details(websocket)
    filepath, _ = _get_log_file_path(log_id)
    try:
        if jinad_args.no_fluentd:
            daemon_logger.warning(
                f'{client_details} asked for logstreaming but fluentd is not available'
            )
            return

        # on connection the fluentd file may not flushed (aka exist) yet
        n = 0
        while not Path(filepath).is_file():
            daemon_logger.info(f'still waiting {filepath} to be ready...')
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
