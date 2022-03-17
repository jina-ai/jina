import argparse
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List

from jina.clients.request import request_generator
from jina.enums import DataInputType, WebsocketSubProtocols
from jina.importer import ImportExtensions
from jina.logging.logger import JinaLogger
from jina.types.request.data import DataRequest

if TYPE_CHECKING:
    from jina.serve.networking import GrpcConnectionPool
    from jina.serve.runtimes.gateway.graph.topology_graph import TopologyGraph


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

    from jina.serve.runtimes.gateway.http.models import JinaEndpointRequestModel

    with ImportExtensions(required=True):
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect

    class ConnectionManager:
        def __init__(self):
            self.active_connections: List[WebSocket] = []
            self.protocol_dict: Dict[str, WebsocketSubProtocols] = {}

        def get_client(self, websocket: WebSocket) -> str:
            return f'{websocket.client.host}:{websocket.client.port}'

        def get_subprotocol(self, headers: Dict):
            try:
                if 'sec-websocket-protocol' in headers:
                    subprotocol = WebsocketSubProtocols(
                        headers['sec-websocket-protocol']
                    )
                elif b'sec-websocket-protocol' in headers:
                    subprotocol = WebsocketSubProtocols(
                        headers[b'sec-websocket-protocol'].decode()
                    )
                else:
                    subprotocol = WebsocketSubProtocols.JSON
                    logger.debug(
                        f'No protocol headers passed. Choosing default subprotocol {WebsocketSubProtocols.JSON}'
                    )
            except Exception as e:
                logger.debug(
                    f'Got an exception while setting user\'s subprotocol, defaulting to JSON {e}'
                )
                subprotocol = WebsocketSubProtocols.JSON
            return subprotocol

        async def connect(self, websocket: WebSocket):
            await websocket.accept()
            subprotocol = self.get_subprotocol(dict(websocket.scope['headers']))
            logger.info(
                f'client {websocket.client.host}:{websocket.client.port} connected '
                f'with subprotocol {subprotocol}'
            )
            self.active_connections.append(websocket)
            self.protocol_dict[self.get_client(websocket)] = subprotocol

        def disconnect(self, websocket: WebSocket):
            self.protocol_dict.pop(self.get_client(websocket))
            self.active_connections.remove(websocket)

        async def receive(self, websocket: WebSocket) -> Any:
            subprotocol = self.protocol_dict[self.get_client(websocket)]
            if subprotocol == WebsocketSubProtocols.JSON:
                return await websocket.receive_json(mode='text')
            elif subprotocol == WebsocketSubProtocols.BYTES:
                return await websocket.receive_bytes()

        async def iter(self, websocket: WebSocket) -> AsyncIterator[Any]:
            try:
                while True:
                    yield await self.receive(websocket)
            except WebSocketDisconnect:
                pass

        async def send(self, websocket: WebSocket, data: DataRequest) -> None:
            subprotocol = self.protocol_dict[self.get_client(websocket)]
            if subprotocol == WebsocketSubProtocols.JSON:
                return await websocket.send_json(data.to_dict(), mode='text')
            elif subprotocol == WebsocketSubProtocols.BYTES:
                return await websocket.send_bytes(data.to_bytes())

    manager = ConnectionManager()

    app = FastAPI()

    from jina.serve.runtimes.gateway.request_handling import (
        handle_request,
        handle_result,
    )
    from jina.serve.stream import RequestStreamer

    streamer = RequestStreamer(
        args=args,
        request_handler=handle_request(
            graph=topology_graph, connection_pool=connection_pool
        ),
        result_handler=handle_result,
    )
    streamer.Call = streamer.stream

    @app.on_event('shutdown')
    async def _shutdown():
        await connection_pool.close()

    @app.websocket('/')
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)

        async def req_iter():
            async for request in manager.iter(websocket):
                if isinstance(request, dict):
                    if request == {}:
                        break
                    else:
                        # NOTE: Helps in converting camelCase to snake_case
                        req_generator_input = JinaEndpointRequestModel(**request).dict()
                        req_generator_input['data_type'] = DataInputType.DICT
                        if request['data'] is not None and 'docs' in request['data']:
                            req_generator_input['data'] = req_generator_input['data'][
                                'docs'
                            ]

                        # you can't do `yield from` inside an async function
                        for data_request in request_generator(**req_generator_input):
                            yield data_request
                elif isinstance(request, bytes):
                    if request == bytes(True):
                        break
                    else:
                        yield DataRequest(request)

        try:
            async for msg in streamer.stream(request_iterator=req_iter()):
                await manager.send(websocket, msg)
        except WebSocketDisconnect:
            logger.info('Client successfully disconnected from server')
            manager.disconnect(websocket)

    return app
