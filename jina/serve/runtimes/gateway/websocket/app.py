import argparse
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional

from jina.clients.request import request_generator
from jina.enums import DataInputType, WebsocketSubProtocols
from jina.excepts import InternalNetworkError
from jina.importer import ImportExtensions
from jina.logging.logger import JinaLogger
from jina.types.request.data import DataRequest

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry

    from jina.serve.networking import GrpcConnectionPool
    from jina.serve.runtimes.gateway.graph.topology_graph import TopologyGraph


def get_fastapi_app(
    args: 'argparse.Namespace',
    topology_graph: 'TopologyGraph',
    connection_pool: 'GrpcConnectionPool',
    logger: 'JinaLogger',
    metrics_registry: Optional['CollectorRegistry'] = None,
):
    """
    Get the app from FastAPI as the Websocket interface.

    :param args: passed arguments.
    :param topology_graph: topology graph that manages the logic of sending to the proper executors.
    :param connection_pool: Connection Pool to handle multiple replicas and sending to different of them
    :param logger: Jina logger.
    :param metrics_registry: optional metrics registry for prometheus used if we need to expose metrics from the executor or from the data request handler
    :return: fastapi app
    """

    from jina.serve.runtimes.gateway.http.models import JinaEndpointRequestModel

    with ImportExtensions(required=True):
        from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect, status

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
                        f'no protocol headers passed. Choosing default subprotocol {WebsocketSubProtocols.JSON}'
                    )
            except Exception as e:
                logger.debug(
                    f'got an exception while setting user\'s subprotocol, defaulting to JSON {e}'
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

    from jina.serve.runtimes.gateway.request_handling import RequestHandler
    from jina.serve.stream import RequestStreamer

    request_handler = RequestHandler(metrics_registry)

    streamer = RequestStreamer(
        args=args,
        request_handler=request_handler.handle_request(
            graph=topology_graph, connection_pool=connection_pool
        ),
        result_handler=request_handler.handle_result(),
    )

    streamer.Call = streamer.stream

    @app.on_event('shutdown')
    async def _shutdown():
        await connection_pool.close()

    @app.websocket('/')
    async def websocket_endpoint(websocket: WebSocket, response: Response):
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
        except InternalNetworkError as err:
            response.status_code = status.WS_1011_INTERNAL_ERROR
            result = DataRequest().to_dict()
            result['header'] = _generate_exception_header(
                err
            )  # attach exception details to response header
            logger.error(
                f'Error while getting responses from deployments: {err.details()}'
            )
            await manager.send(websocket, DataRequest(result))
            manager.disconnect(websocket)
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except WebSocketDisconnect:
            logger.info('Client successfully disconnected from server')
            manager.disconnect(websocket)

    def _generate_exception_header(error: InternalNetworkError):
        import traceback

        exception_dict = {
            'name': str(error.__class__),
            'stacks': [
                str(x) for x in traceback.extract_tb(error.og_exception.__traceback__)
            ],
            'executor': '',
        }
        status_dict = {
            'code': 3,  # status error
            'description': error.details() if error.details() else '',
            'exception': exception_dict,
        }
        header_dict = {'request_id': error.request_id, 'status': status_dict}
        return header_dict

    return app
