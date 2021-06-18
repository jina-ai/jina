import argparse
from typing import List

from ....zmq import AsyncZmqlet
from .....importer import ImportExtensions
from .....logging.logger import JinaLogger
from .....types.message import Message


def get_fastapi_app(args: 'argparse.Namespace', logger: 'JinaLogger'):
    """
    Get the app from FastAPI as the Websocket interface.

    :param args: passed arguments.
    :param logger: Jina logger.
    :return: fastapi app
    """

    with ImportExtensions(required=True):
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect

    class ConnectionManager:
        def __init__(self):
            self.active_connections: List[WebSocket] = []

        async def connect(self, websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)

        def disconnect(self, websocket: WebSocket):
            self.active_connections.remove(websocket)

    manager = ConnectionManager()

    app = FastAPI()

    zmqlet = AsyncZmqlet(args, logger)

    @app.on_event('shutdown')
    def _shutdown():
        zmqlet.close()

    @app.websocket('/')
    async def websocket_endpoint(websocket: WebSocket):

        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_bytes()
                if data == bytes(True):
                    continue
                await zmqlet.send_message(Message(None, data, 'gateway', **vars(args)))
                msg = await zmqlet.recv_message()
                await websocket.send_bytes(msg.response.binary_str())
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    return app
