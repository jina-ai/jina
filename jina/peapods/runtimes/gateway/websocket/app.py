import argparse
import inspect
from typing import List

from ....grpc import Grpclet
from ....zmq import AsyncZmqlet
from .....importer import ImportExtensions
from .....logging.logger import JinaLogger
from .....types.request import Request


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
            logger.debug(
                f'client {websocket.client.host}:{websocket.client.port} connected'
            )
            self.active_connections.append(websocket)

        def disconnect(self, websocket: WebSocket):
            self.active_connections.remove(websocket)

    manager = ConnectionManager()

    app = FastAPI()

    if args.grpc_data_requests:
        from ....stream.gateway import GrpcGatewayStreamer

        iolet = Grpclet(
            args=args,
            message_callback=None,
            logger=logger,
        )
        streamer = GrpcGatewayStreamer(args, iolet)
    else:
        from ....stream.gateway import ZmqGatewayStreamer

        iolet = AsyncZmqlet(args, logger)
        streamer = ZmqGatewayStreamer(args, iolet)

    @app.on_event('shutdown')
    async def _shutdown():
        if inspect.iscoroutinefunction(iolet.close):
            await iolet.close()
        else:
            iolet.close()

    @app.websocket('/')
    async def websocket_endpoint(websocket: WebSocket):

        await manager.connect(websocket)

        async def req_iter():
            async for request_bytes in websocket.iter_bytes():
                if request_bytes == bytes(True):
                    break
                yield Request(request_bytes)

        try:
            async for msg in streamer.stream(request_iterator=req_iter()):
                await websocket.send_bytes(bytes(msg))
        except WebSocketDisconnect:
            logger.debug('Client successfully disconnected from server')
            manager.disconnect(websocket)

    return app
