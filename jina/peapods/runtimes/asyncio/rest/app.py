import argparse
import asyncio
from typing import Any

from google.protobuf.json_format import MessageToDict

from ..grpc.async_call import AsyncPrefetchCall
from ....zmq import AsyncZmqlet
from .....clients.request import request_generator
from .....enums import RequestType
from .....importer import ImportExtensions
from .....logging import JinaLogger
from .....types.message import Message
from .....types.request import Request

def get_fastapi_app(args: 'argparse.Namespace', logger: 'JinaLogger'):
    with ImportExtensions(required=True):
        from fastapi import FastAPI, WebSocket, Body
        from fastapi.responses import JSONResponse
        from fastapi.middleware.cors import CORSMiddleware
        from starlette.endpoints import WebSocketEndpoint
        from starlette import status
        from starlette.types import Receive, Scope, Send

    app = FastAPI(title='RESTRuntime')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
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
        from .....clients import BaseClient
        BaseClient.add_default_kwargs(body)
        req_iter = request_generator(**body)
        results = await get_result_in_json(req_iter=req_iter)
        return JSONResponse(content=results[0], status_code=200)

    async def get_result_in_json(req_iter):
        return [MessageToDict(k) async for k in servicer.Call(request_iterator=req_iter, context=None)]

    @app.websocket_route(path='/stream')
    class StreamingEndpoint(WebSocketEndpoint):
        """
        :meth:`handle_receive()`
            Await a message on :meth:`websocket.receive()`
            Send the message to zmqlet via :meth:`zmqlet.send_message()` and await
        :meth:`handle_send()`
            Await a message on :meth:`zmqlet.recv_message()`
            Send the message back to client via :meth:`websocket.send()` and await
        :meth:`dispatch()`
            Awaits on concurrent tasks :meth:`handle_receive()` & :meth:`handle_send()`
            This makes sure gateway is nonblocking
        Await exit strategy:
            :meth:`handle_receive()` keeps track of num_requests received
            :meth:`handle_send()` keeps track of num_responses sent
            Client sends a final message: `bytes(True)` to indicate request iterator is empty
            Server exits out of await when `(num_requests == num_responses != 0 and is_req_empty)`
        """

        encoding = None
        is_req_empty = False
        num_requests = 0
        num_responses = 0

        def __init__(self, scope: 'Scope', receive: 'Receive', send: 'Send') -> None:
            super().__init__(scope, receive, send)
            self.args = args
            self.name = args.name or self.__class__.__name__
            self.client_encoding = None

        async def dispatch(self) -> None:
            websocket = WebSocket(self.scope, receive=self.receive, send=self.send)
            await self.on_connect(websocket)
            close_code = status.WS_1000_NORMAL_CLOSURE

            await asyncio.gather(
                self.handle_receive(websocket=websocket, close_code=close_code),
                self.handle_send(websocket=websocket)
            )

        async def on_connect(self, websocket: WebSocket) -> None:
            # TODO(Deepankar): To enable multiple concurrent clients,
            # Register each client - https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients
            # And move class variables to instance variable
            await websocket.accept()
            self.client_info = f'{websocket.client.host}:{websocket.client.port}'
            logger.success(f'Client {self.client_info} connected to stream requests via websockets')
            self.zmqlet = AsyncZmqlet(args, logger)

        async def handle_receive(self, websocket: WebSocket, close_code: int) -> None:
            try:
                while True:
                    message = await websocket.receive()
                    if message['type'] == 'websocket.receive':
                        data = await self.decode(websocket, message)
                        if data == bytes(True):
                            self.is_req_empty = True
                            continue
                        await self.zmqlet.send_message(
                            Message(None, Request(data), 'gateway', **vars(self.args))
                        )
                        self.num_requests += 1
                    elif message['type'] == 'websocket.disconnect':
                        close_code = int(message.get('code', status.WS_1000_NORMAL_CLOSURE))
                        break
            except Exception as exc:
                close_code = status.WS_1011_INTERNAL_ERROR
                logger.error(f'Got an exception in handle_receive: {exc!r}')
                raise exc from None
            finally:
                await self.on_disconnect(websocket, close_code)

        async def handle_send(self, websocket: WebSocket) -> None:

            def handle_route(msg: 'Message') -> 'Request':
                msg.add_route(self.name, hex(id(self)))
                return msg.response

            try:
                while not (self.num_requests == self.num_responses != 0 and self.is_req_empty):
                    response = await self.zmqlet.recv_message(callback=handle_route)
                    if self.client_encoding == 'bytes':
                        await websocket.send_bytes(response.SerializeToString())
                    else:
                        await websocket.send_json(response.to_json())
                    self.num_responses += 1
            except Exception as e:
                logger.error(f'Got an exception in handle_send: {e!r}')

        async def decode(self, websocket: WebSocket, message: Message) -> Any:
            if 'text' in message or 'json' in message:
                self.client_encoding = 'text'

            if 'bytes' in message:
                self.client_encoding = 'bytes'

            return await super().decode(websocket, message)

        async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
            self.zmqlet.close()
            logger.info(f'Client {self.client_info} got disconnected!')

    return app
