import asyncio
from typing import Any

from google.protobuf.json_format import MessageToDict

from ..... import clients
from ....zmq import AsyncZmqlet
from .....enums import RequestType
from .....types.message import Message
from .....types.request import Request
from .....importer import ImportExtensions
from ..grpc.async_call import AsyncPrefetchCall


def get_fastapi_app(args, logger):
    with ImportExtensions(required=True):
        from fastapi import FastAPI, Body
        from fastapi import WebSocket, WebSocketDisconnect
        from fastapi.responses import JSONResponse
        from fastapi.middleware.cors import CORSMiddleware
        # TODO(Deepankar): starlette comes installed with fastapi. Should this be added as a separate dependency?
        from starlette.endpoints import WebSocketEndpoint
        if False:
            from starlette.types import Receive, Scope, Send

    app = FastAPI(title='RESTGateway')
    app.add_middleware(CORSMiddleware, allow_origins=['*'])
    servicer = AsyncPrefetchCall(args)

    def error(reason, status_code):
        return JSONResponse(content={'reason': reason}, status_code=status_code)


    @app.get('/ready')
    async def is_ready():
        return JSONResponse(status_code=200)


    @app.post(path='/api/{mode}')
    async def api(mode: str, body: Any = Body(...)):
        if mode.upper() not in RequestType.__members__:
            return error(reason=f'unsupported mode {mode}', status_code=405)

        if 'data' not in body:
            return error('"data" field is empty', 406)

        body['mode'] = RequestType.from_string(mode)
        request_iterator = getattr(clients.request, mode)(**body)
        results = await get_result_in_json(request_iterator=request_iterator)
        return JSONResponse(content=results[0], status_code=200)

    async def get_result_in_json(request_iterator):
        return [MessageToDict(k) async for k in servicer.Call(request_iterator=request_iterator, context=None)]


    @app.websocket_route(path='/stream')
    class StreamingEndpoint(WebSocketEndpoint):

        # This disabled other encodings ('text' & 'json')
        encoding = 'bytes'

        def __init__(self, scope: 'Scope', receive: 'Receive', send: 'Send') -> None:
            super().__init__(scope, receive, send)
            self.args = args
            self.name = args.name or self.__class__.__name__

        def handle(self, msg: 'Message') -> 'Request':
            msg.add_route(self.name, self.args.identity)
            return msg.response

        async def on_connect(self, websocket: WebSocket) -> None:
            await websocket.accept()
            self.client_info = f'{websocket.client.host}:{websocket.client.port}'
            logger.success(f'Client {self.client_info} connected to stream requests via websockets')
            self.zmqlet = AsyncZmqlet(args, logger)

        async def on_receive(self, websocket: WebSocket, data: Any) -> None:
            # At any point only a single request is sent in bytes instead of an iterator of requests
            # For each such request, we send back the response in bytes
            try:
                asyncio.create_task(
                    self.zmqlet.send_message(
                        Message(None, data, 'gateway', **vars(self.args))
                    )
                )
                response = await self.zmqlet.recv_message(callback=self.handle)
                # Convert to bytes before sending the response
                await websocket.send_bytes(response.SerializeToString())
            except Exception as e:
                logger.error(f'Got an exception while streaming requests: {e}')
                return

        async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
            self.zmqlet.close()
            logger.info(f'Client {self.client_info} got disconnected!')

    return app
