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

from ... import daemon_logger, jinad_args
from ...helper import get_log_file_path
from ...models import DaemonID
from ...stores import get_store_from_id

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


@router.websocket('/logstream/{log_id}')
async def _logstream(websocket: WebSocket, log_id: DaemonID, timeout: int = 60):
    manager = ConnectionManager()
    await manager.connect(websocket)
    client_details = _websocket_details(websocket)
    filepath, _ = get_log_file_path(log_id)
    try:
        if jinad_args.no_fluentd:
            daemon_logger.warning(
                f'{client_details} asked for logstreaming but fluentd is not available'
            )
            return

        # on connection the fluentd file may not flushed (aka exist) yet
        n = 0
        while (
            not Path(filepath).is_file()
            and websocket.application_state == WebSocketState.CONNECTED
        ):
            if n % 10 == 0:
                daemon_logger.debug(f'still waiting {filepath} to be ready...')
            await asyncio.sleep(1)
            n += 1
            if timeout > 0 and n >= timeout:
                daemon_logger.error(
                    f'waited for {timeout} secs for {filepath} to be ready, exiting'
                )
                return

        daemon_logger.success(f'{filepath} is ready for streaming')

        with open(filepath) as fp:
            fp.seek(0, 2)
            delay = 0.2
            n = 0
            while manager._has_active_connections():
                line = fp.readline()  # also possible to read an empty line
                if line:
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
