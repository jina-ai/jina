import asyncio
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl

from fastapi import APIRouter, WebSocket
from starlette.endpoints import WebSocketEndpoint
from starlette.types import Receive, Scope, Send

from ... import daemon_logger
from ...config import log_config
from ...excepts import NoSuchFileException

router = APIRouter()


async def tail(file_handler, line_num_from=0, timeout=5):
    """ asynchronous tail file """
    line_number = 0
    last_log_time = time.time()
    while time.time() - last_log_time < timeout:
        for line in file_handler:
            line_number += 1
            if line_number < line_num_from:
                continue
            yield line_number, line
            last_log_time = time.time()
            await asyncio.sleep(0.01)
    else:
        daemon_logger.debug(f'File tailer timed-out!')
        yield None, None


class LogStreamingEndpoint(WebSocketEndpoint):
    """
    WebSocket based streaming for FluentD logs written by remote Peas/Pods/Flows.

    - URL - ws://{server}:{port}/logstream/{log_id}/?timeout={timeout}
    - Mandatory param - {log_id} (If a folder with {log__id} doesn't exist, it disconnects the client with code = 1006)
    - Optional param - {timeout} (Defaults to DEFAULT_TIMEOUT)

    Server
        1. Waits for the client to send a json `{'from': line_number}`.
        2. Tails file & streams one log line at a time in a loop.
        3. Waits max `timeout` secs b/w 2 suucessive log lines.
        4. In case of timeout, sends {'code': TIMEOUT_ERROR_CODE} & waits step 1.

    Client
        1. Connects to the server & send a json `{'from': 0}`.
        2. Reads & processes streamed logs e.g. - `await websocket.receive()` in a loop.
        3. Wait for a message {'code': TIMEOUT_ERROR_CODE} indicating timeout.
        4. Goes back to step 1 if client still expects logs.

    """

    encoding = 'json'
    DEFAULT_TIMEOUT = 5
    TIMEOUT_ERROR_CODE = 4000
    NO_FILE_ERROR_CODE = 4001

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        super().__init__(scope, receive, send)

        # Accessing path / query params from scope in ASGI
        # https://asgi.readthedocs.io/en/latest/specs/www.html#websocket-connection-scope
        self.log_id = self.scope.get('path').split('/')[-1]
        self.filepath = log_config.PATH % self.log_id
        query_string = self.scope.get('query_string').decode()
        self.timeout = float(dict(parse_qsl(query_string)).get('timeout', self.DEFAULT_TIMEOUT))

        self.active_clients = []

    async def on_connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        # FastAPI & Starlette still don't have a generic WebSocketException
        # https://github.com/encode/starlette/pull/527
        # The following `raise` raises `websockets.exceptions.ConnectionClosedError` (code = 1006)
        # TODO(Deepankar): This needs better handling.
        if not Path(self.filepath).is_file():
            raise NoSuchFileException(f'File {self.filepath} not found locally')

        self.active_clients.append(websocket)
        self.client_details = f'{websocket.client.host}:{websocket.client.port}'
        daemon_logger.info(f'Client {self.client_details} got connected to stream Fluentd logs!')

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        if not Path(self.filepath).is_file():
            raise NoSuchFileException(f'File {self.filepath} not found locally')

        line_num_from = int(data.get('from', 0))
        with open(self.filepath) as fp:
            logs_to_be_sent = {}
            async for line_number, line in tail(file_handler=fp, line_num_from=line_num_from, timeout=self.timeout):
                if not line_number:
                    await websocket.send_json({"code": self.TIMEOUT_ERROR_CODE})
                    break
                logs_to_be_sent[line_number] = line
                daemon_logger.info(f'Sending logs {logs_to_be_sent}')
                await websocket.send_json(logs_to_be_sent)
                logs_to_be_sent = {}

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        self.active_clients.remove(websocket)
        daemon_logger.info(f'Client {self.client_details} got disconnected!')


# TODO: adding websocket in this way do not generate any docs
#  see: https://github.com/tiangolo/fastapi/issues/1983
router.add_websocket_route(path='/logstream/{log_id}',
                           endpoint=LogStreamingEndpoint)
