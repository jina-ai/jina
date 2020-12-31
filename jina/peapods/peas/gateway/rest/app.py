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
        from fastapi import FastAPI, WebSocket, Body
        from fastapi.responses import JSONResponse
        from fastapi.middleware.cors import CORSMiddleware
        # TODO(Deepankar): starlette comes installed with fastapi. Should this be added as a separate dependency?
        from starlette import status
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
        """
        :meth:`handle_receive`
            await a message on :meth:`websocket.receive()`
            send the message to zmqlet via :meth:`zmqlet.send_message()` and await
        :meth:`handle_send`
            await a message on :meth:`zmqlet.recv_message()`
            send the message back to client via :meth:`websocket.send()` and await
        :meth:`dispatch`
            starts an independent task :meth:`handle_receive`
            awaits on :meth:`handle_send`
            this makes sure gateway is nonblocking
        await exit strategy:
            :meth:`handle_receive` keeps track of num_requests received
            :meth:`handle_send` keeps track of num_responses sent
            client sends a final message: `bytes(True)` to indicate request iterator is empty
            server exits out of await when `(num_requests == num_responses != 0 and is_req_empty)`
        """

        # TODO(Deepankar): This disables other encodings - 'text' & 'json'. Enable json based encoding
        encoding = 'bytes'
        is_req_empty = False
        num_requests = 0
        num_responses = 0

        def __init__(self, scope: 'Scope', receive: 'Receive', send: 'Send') -> None:
            super().__init__(scope, receive, send)
            self.args = args
            self.name = args.name or self.__class__.__name__

        async def dispatch(self) -> None:
            websocket = WebSocket(self.scope, receive=self.receive, send=self.send)
            await self.on_connect(websocket)
            close_code = status.WS_1000_NORMAL_CLOSURE

            asyncio.create_task(
                self.handle_receive(websocket=websocket, close_code=close_code)
            )
            await self.handle_send(websocket=websocket)

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

                    if message["type"] == "websocket.receive":
                        data = await self.decode(websocket, message)
                        if data == bytes(True):
                            self.is_req_empty = True
                            continue
                        await self.zmqlet.send_message(
                            Message(None, Request(data), 'gateway', **vars(self.args))
                        )
                        self.num_requests += 1
                    elif message["type"] == "websocket.disconnect":
                        close_code = int(message.get("code", status.WS_1000_NORMAL_CLOSURE))
                        break
            except Exception as exc:
                close_code = status.WS_1011_INTERNAL_ERROR
                logger.error(f'Got an exception in handle_receive: {repr(exc)}')
                raise exc from None
            finally:
                await self.on_disconnect(websocket, close_code)

        async def handle_send(self, websocket: WebSocket) -> None:

            def handle_route(msg: 'Message') -> 'Request':
                msg.add_route(self.name, self.args.identity)
                return msg.response

            try:
                while not (self.num_requests == self.num_responses != 0 and self.is_req_empty):
                    response = await self.zmqlet.recv_message(callback=handle_route)
                    await websocket.send_bytes(response.SerializeToString())
                    self.num_responses += 1
            except Exception as e:
                logger.error(f'Got an exception in handle_send: {repr(e)}')

        async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
            self.zmqlet.close()
            logger.info(f'Client {self.client_info} got disconnected!')

    return app
