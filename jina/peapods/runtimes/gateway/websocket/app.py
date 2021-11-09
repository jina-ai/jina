import argparse
from typing import List, TYPE_CHECKING

from .....importer import ImportExtensions
from .....logging.logger import JinaLogger
from .....types.request import Request

if TYPE_CHECKING:
    from ..graph.topology_graph import TopologyGraph
    from ....networking import GrpcConnectionPool


def get_fastapi_app(
    args: 'argparse.Namespace',
    topology_graph: 'TopologyGraph',
    connection_pool: 'GrpcConnectionPool',
    logger: 'JinaLogger',
):
    """
    Get the app from FastAPI as the Websocket interface.

    :param args: passed arguments.
    :param topology_graph: topology graph that manages the logic of sending to the proper executors.
    :param connection_pool: Connection Pool to handle multiple replicas and sending to different of them
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

    from ....stream.gateway import GatewayStreamer

    streamer = GatewayStreamer(
        args, graph=topology_graph, connection_pool=connection_pool
    )

    @app.on_event('shutdown')
    async def _shutdown():
        connection_pool.close()

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
