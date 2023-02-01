import argparse
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional, Union

from jina.clients.request import request_generator
from jina.enums import DataInputType, WebsocketSubProtocols
from jina.excepts import InternalNetworkError
from jina.helper import get_full_version
from jina.importer import ImportExtensions
from jina.logging.logger import JinaLogger
from jina.types.request.data import DataRequest
from jina.types.request.status import StatusMessage

if TYPE_CHECKING:  # pragma: no cover
    from opentelemetry import trace

    from jina.serve.streamer import GatewayStreamer


def _fits_ws_close_msg(msg: str):
    # Websocket close messages ('reasons') can't exceed 123 bytes:
    # https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/close
    ws_closing_msg_max_len = 123
    return len(msg.encode('utf-8')) <= ws_closing_msg_max_len


def get_fastapi_app(
    streamer: 'GatewayStreamer',
    logger: 'JinaLogger',
    tracing: Optional[bool] = None,
    tracer_provider: Optional['trace.TracerProvider'] = None,
):
    """
    Get the app from FastAPI as the Websocket interface.

    :param streamer: gateway streamer object.
    :param logger: Jina logger.
    :param tracing: Enables tracing is set to True.
    :param tracer_provider: If tracing is enabled the tracer_provider will be used to instrument the code.
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

        async def send(
            self, websocket: WebSocket, data: Union[DataRequest, StatusMessage]
        ) -> None:
            subprotocol = self.protocol_dict[self.get_client(websocket)]
            if subprotocol == WebsocketSubProtocols.JSON:
                return await websocket.send_json(data.to_dict(), mode='text')
            elif subprotocol == WebsocketSubProtocols.BYTES:
                return await websocket.send_bytes(data.to_bytes())

    manager = ConnectionManager()

    app = FastAPI()

    if tracing:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    @app.get(
        path='/',
        summary='Get the health of Jina service',
    )
    async def _health():
        """
        Get the health of this Jina service.
        .. # noqa: DAR201

        """
        return {}

    @app.get(
        path='/status',
        summary='Get the status of Jina service',
    )
    async def _status():
        """
        Get the status of this Jina service.

        This is equivalent to running `jina -vf` from command line.

        .. # noqa: DAR201
        """
        version, env_info = get_full_version()
        for k, v in version.items():
            version[k] = str(v)
        for k, v in env_info.items():
            env_info[k] = str(v)
        return {'jina': version, 'envs': env_info}

    @app.on_event('shutdown')
    async def _shutdown():
        await streamer.close()

    @app.websocket('/')
    async def websocket_endpoint(
        websocket: WebSocket, response: Response
    ):  # 'response' is a FastAPI response, not a Jina response
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
            import grpc

            manager.disconnect(websocket)
            fallback_msg = (
                f'Connection to deployment at {err.dest_addr} timed out. You can adjust `timeout_send` attribute.'
                if err.code() == grpc.StatusCode.DEADLINE_EXCEEDED
                else f'Network error while connecting to deployment at {err.dest_addr}. It may be down.'
            )
            msg = (
                err.details()
                if _fits_ws_close_msg(
                    err.details()
                )  # some messages are too long for ws closing message
                else fallback_msg
            )
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=msg)
        except WebSocketDisconnect:
            logger.info('Client successfully disconnected from server')
            manager.disconnect(websocket)

    async def _get_singleton_result(request_iterator) -> Dict:
        """
        Streams results from AsyncPrefetchCall as a dict

        :param request_iterator: request iterator, with length of 1
        :return: the first result from the request iterator
        """
        async for k in streamer.stream(request_iterator=request_iterator):
            request_dict = k.to_dict()
            return request_dict

    from jina._docarray import DocumentArray
    from jina.proto import jina_pb2
    from jina.serve.executors import __dry_run_endpoint__
    from jina.serve.runtimes.gateway.http.models import PROTO_TO_PYDANTIC_MODELS

    @app.get(
        path='/dry_run',
        summary='Get the readiness of Jina Flow service, sends an empty DocumentArray to the complete Flow to '
        'validate connectivity',
        response_model=PROTO_TO_PYDANTIC_MODELS.StatusProto,
    )
    async def _dry_run_http():
        """
        Get the health of the complete Flow service.
        .. # noqa: DAR201

        """

        da = DocumentArray([])

        try:
            _ = await _get_singleton_result(
                request_generator(
                    exec_endpoint=__dry_run_endpoint__,
                    data=da,
                    data_type=DataInputType.DOCUMENT,
                )
            )
            status_message = StatusMessage()
            status_message.set_code(jina_pb2.StatusProto.SUCCESS)
            return status_message.to_dict()
        except Exception as ex:
            status_message = StatusMessage()
            status_message.set_exception(ex)
            return status_message.to_dict(use_integers_for_enums=True)

    @app.websocket('/dry_run')
    async def websocket_endpoint(
        websocket: WebSocket, response: Response
    ):  # 'response' is a FastAPI response, not a Jina response
        from jina.proto import jina_pb2
        from jina.serve.executors import __dry_run_endpoint__

        await manager.connect(websocket)

        da = DocumentArray([])
        try:
            async for _ in streamer.stream(
                request_iterator=request_generator(
                    exec_endpoint=__dry_run_endpoint__,
                    data=da,
                    data_type=DataInputType.DOCUMENT,
                )
            ):
                pass
            status_message = StatusMessage()
            status_message.set_code(jina_pb2.StatusProto.SUCCESS)
            await manager.send(websocket, status_message)
        except InternalNetworkError as err:
            manager.disconnect(websocket)
            msg = (
                err.details()
                if _fits_ws_close_msg(err.details())  # some messages are too long
                else f'Network error while connecting to deployment at {err.dest_addr}. It may be down.'
            )
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=msg)
        except WebSocketDisconnect:
            logger.info('Client successfully disconnected from server')
            manager.disconnect(websocket)
        except Exception as ex:
            manager.disconnect(websocket)
            status_message = StatusMessage()
            status_message.set_exception(ex)
            await manager.send(websocket, status_message)

    return app
