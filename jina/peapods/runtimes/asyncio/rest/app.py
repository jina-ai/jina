import argparse
import asyncio
import warnings
from typing import Any

from google.protobuf.json_format import MessageToDict

from ..grpc.async_call import AsyncPrefetchCall
from ....zmq import AsyncZmqlet
from ..... import __version__
from .....clients.request import request_generator
from .....enums import RequestType
from .....helper import get_full_version, random_identity
from .....importer import ImportExtensions
from .....logging import JinaLogger, default_logger
from .....logging.profile import used_memory_readable
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
        from starlette.responses import StreamingResponse
        from .models import JinaStatusModel, JinaIndexRequestModel, JinaDeleteRequestModel, JinaUpdateRequestModel, \
            JinaSearchRequestModel

    app = FastAPI(
        title='Jina',
        description='REST interface for Jina',
        version=__version__,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    zmqlet = AsyncZmqlet(args, default_logger)
    servicer = AsyncPrefetchCall(args, zmqlet)

    def error(reason, status_code):
        return JSONResponse(content={'reason': reason}, status_code=status_code)

    @app.on_event('shutdown')
    def _shutdown():
        zmqlet.close()

    @app.on_event('startup')
    async def startup():
        default_logger.info(f'''
    Jina REST interface
    💬 Swagger UI:\thttp://localhost:{args.port_expose}/docs
    📚 Redoc     :\thttp://localhost:{args.port_expose}/redoc
        ''')
        from jina import __ready_msg__
        default_logger.success(__ready_msg__)

    @app.get(path='/status',
             summary='Get the status of Jina',
             response_model=JinaStatusModel,
             tags=['jina']
             )
    async def _status():
        _info = get_full_version()
        return {
            'jina': _info[0],
            'envs': _info[1],
            'used_memory': used_memory_readable()
        }

    @app.post(path='/api/{mode}', deprecated=True)
    async def api(mode: str, body: Any = Body(...)):
        warnings.warn('this interface will be retired soon', DeprecationWarning)
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

    @app.post(path='/index',
              summary='Index documents into Jina',
              tags=['CRUD']
              )
    async def index_api(body: JinaIndexRequestModel):
        from .....clients import BaseClient
        bd = body.dict()
        bd['mode'] = RequestType.INDEX
        BaseClient.add_default_kwargs(bd)
        return StreamingResponse(result_in_stream(request_generator(**bd)))

    @app.post(path='/search',
              summary='Search documents from Jina',
              tags=['CRUD']
              )
    async def index_api(body: JinaSearchRequestModel):
        from .....clients import BaseClient
        bd = body.dict()
        bd['mode'] = RequestType.SEARCH
        BaseClient.add_default_kwargs(bd)
        return StreamingResponse(result_in_stream(request_generator(**bd)))

    @app.put(path='/update',
             summary='Update documents in Jina',
             tags=['CRUD']
             )
    async def index_api(body: JinaUpdateRequestModel):
        from .....clients import BaseClient
        bd = body.dict()
        bd['mode'] = RequestType.UPDATE
        BaseClient.add_default_kwargs(bd)
        return StreamingResponse(result_in_stream(request_generator(**bd)))

    @app.delete(path='/delete',
                summary='Delete documents in Jina',
                tags=['CRUD']
                )
    async def index_api(body: JinaDeleteRequestModel):
        from .....clients import BaseClient
        bd = body.dict()
        bd['mode'] = RequestType.DELETE
        BaseClient.add_default_kwargs(bd)
        return StreamingResponse(result_in_stream(request_generator(**bd)))

    async def result_in_stream(req_iter):
        async for k in servicer.Call(request_iterator=req_iter, context=None):
            yield MessageToDict(k)

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

        def __init__(self, scope: 'Scope', receive: 'Receive', send: 'Send') -> None:
            super().__init__(scope, receive, send)
            self.args = args
            self.name = args.name or self.__class__.__name__
            self._id = random_identity()
            self.client_encoding = None

        async def dispatch(self) -> None:
            websocket = WebSocket(self.scope, receive=self.receive, send=self.send)
            await self.on_connect(websocket)
            close_code = status.WS_1000_NORMAL_CLOSURE

            await asyncio.gather(
                self.handle_receive(websocket=websocket, close_code=close_code),
            )

        async def on_connect(self, websocket: WebSocket) -> None:
            # TODO(Deepankar): To enable multiple concurrent clients,
            # Register each client - https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients
            # And move class variables to instance variable
            await websocket.accept()
            self.client_info = f'{websocket.client.host}:{websocket.client.port}'
            logger.success(f'Client {self.client_info} connected to stream requests via websockets')

        async def handle_receive(self, websocket: WebSocket, close_code: int) -> None:
            def handle_route(msg: 'Message') -> 'Request':
                msg.add_route(self.name, self._id)
                return msg.response

            try:
                while True:
                    message = await websocket.receive()
                    if message['type'] == 'websocket.receive':
                        data = await self.decode(websocket, message)
                        if data == bytes(True):
                            await asyncio.sleep(.1)
                            continue
                        await zmqlet.send_message(Message(None, Request(data), 'gateway', **vars(self.args)))
                        response = await zmqlet.recv_message(callback=handle_route)
                        if self.client_encoding == 'bytes':
                            await websocket.send_bytes(response.SerializeToString())
                        else:
                            await websocket.send_json(response.json())
                    elif message['type'] == 'websocket.disconnect':
                        close_code = int(message.get('code', status.WS_1000_NORMAL_CLOSURE))
                        break
            except Exception as exc:
                close_code = status.WS_1011_INTERNAL_ERROR
                logger.error(f'Got an exception in handle_receive: {exc!r}')
                raise
            finally:
                await self.on_disconnect(websocket, close_code)

        async def decode(self, websocket: WebSocket, message: Message) -> Any:
            if 'text' in message or 'json' in message:
                self.client_encoding = 'text'

            if 'bytes' in message:
                self.client_encoding = 'bytes'

            return await super().decode(websocket, message)

        async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
            logger.info(f'Client {self.client_info} got disconnected!')

    return app
