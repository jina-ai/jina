import argparse
import asyncio
from typing import Any, Optional

from google.protobuf.json_format import MessageToJson

from ..grpc.async_call import AsyncPrefetchCall
from ....zmq import AsyncZmqlet
from ..... import __version__
from .....clients.request import request_generator
from .....helper import get_full_version, random_identity
from .....importer import ImportExtensions
from .....logging.logger import JinaLogger
from .....logging.predefined import default_logger
from .....logging.profile import used_memory_readable
from .....types.message import Message
from .....types.request import Request


def get_fastapi_app(args: 'argparse.Namespace', logger: 'JinaLogger'):
    """
    Get the app from FastAPI as the REST interface.

    :param args: passed arguments.
    :param logger: Jina logger.
    :return: fastapi app
    """
    with ImportExtensions(required=True):
        from fastapi import FastAPI, WebSocket
        from fastapi.responses import JSONResponse
        from fastapi.middleware.cors import CORSMiddleware
        from starlette.endpoints import WebSocketEndpoint
        from starlette import status
        from starlette.types import Receive, Scope, Send
        from starlette.responses import StreamingResponse
        from .models import (
            JinaStatusModel,
            JinaIndexRequestModel,
            JinaDeleteRequestModel,
            JinaUpdateRequestModel,
            JinaSearchRequestModel,
            JinaRequestModel,
        )

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
        """
        Get the error code.

        :param reason: content of error
        :param status_code: status code
        :return: error in JSON response
        """
        return JSONResponse(content={'reason': reason}, status_code=status_code)

    @app.on_event('shutdown')
    def _shutdown():
        zmqlet.close()

    @app.on_event('startup')
    async def startup():
        """Log the host information when start the server."""
        default_logger.info(
            f'''
    Jina REST interface
    💬 Swagger UI:\thttp://localhost:{args.port_expose}/docs
    📚 Redoc     :\thttp://localhost:{args.port_expose}/redoc
        '''
        )
        from jina import __ready_msg__

        default_logger.success(__ready_msg__)

    @app.get(
        path='/status',
        summary='Get the status of Jina',
        response_model=JinaStatusModel,
        tags=['Management'],
    )
    async def _status():
        _info = get_full_version()
        return {
            'jina': _info[0],
            'envs': _info[1],
            'used_memory': used_memory_readable(),
        }

    @app.post(
        path='/post/{endpoint:path}',
        summary='Post a data request to some endpoint',
        tags=['Data Request'],
        response_model=JinaRequestModel,
    )
    async def post(endpoint: str, body: Optional[JinaRequestModel] = None):
        """
        Request mode service and return results in JSON, a deprecated interface.

        :param endpoint: the executor endpoint
        :param body: the Request body.
        :return: Results in JSONresponse.
        """

        bd = body.dict() if body else {'data': None}
        bd['exec_endpoint'] = endpoint
        return StreamingResponse(
            result_in_stream(request_generator(**bd)), media_type='application/json'
        )

    @app.post(
        path='/index',
        summary='Post a data request to `/index` endpoint',
        tags=['Sugary CRUD'],
        response_model=JinaIndexRequestModel,
    )
    async def index_api(body: JinaIndexRequestModel):
        """
        Index API to index documents.

        :param body: index request.
        :return: Response of the results.
        """

        bd = body.dict()
        return StreamingResponse(
            result_in_stream(request_generator(**bd)), media_type='application/json'
        )

    @app.post(
        path='/search',
        summary='Post a data request to `/search` endpoint',
        tags=['Sugary CRUD'],
        response_model=JinaSearchRequestModel,
    )
    async def search_api(body: JinaSearchRequestModel):
        """
        Search API to search documents.

        :param body: search request.
        :return: Response of the results.
        """

        bd = body.dict()
        return StreamingResponse(
            result_in_stream(request_generator(**bd)), media_type='application/json'
        )

    @app.put(
        path='/update',
        summary='Post a data request to `/update` endpoint',
        tags=['Sugary CRUD'],
        response_model=JinaUpdateRequestModel,
    )
    async def update_api(body: JinaUpdateRequestModel):
        """
        Update API to update documents.

        :param body: update request.
        :return: Response of the results.
        """

        bd = body.dict()
        return StreamingResponse(
            result_in_stream(request_generator(**bd)), media_type='application/json'
        )

    @app.delete(
        path='/delete',
        summary='Post a data request to `/delete` endpoint',
        tags=['Sugary CRUD'],
        response_model=JinaDeleteRequestModel,
    )
    async def delete_api(body: JinaDeleteRequestModel):
        """
        Delete API to delete documents.

        :param body: delete request.
        :return: Response of the results.
        """

        bd = body.dict()
        return StreamingResponse(
            result_in_stream(request_generator(**bd)), media_type='application/json'
        )

    async def result_in_stream(req_iter):
        """
        Streams results from AsyncPrefetchCall as json

        :param req_iter: request iterator
        :yield: result
        """
        async for k in servicer.Call(request_iterator=req_iter, context=None):
            yield MessageToJson(
                k,
                including_default_value_fields=args.including_default_value_fields,
                preserving_proto_field_name=True,
                sort_keys=args.sort_keys,
                use_integers_for_enums=args.use_integers_for_enums,
                float_precision=args.float_precision,
            )

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
            """Awaits on concurrent tasks :meth:`handle_receive()` & :meth:`handle_send()`"""
            websocket = WebSocket(self.scope, receive=self.receive, send=self.send)
            await self.on_connect(websocket)
            close_code = status.WS_1000_NORMAL_CLOSURE

            await asyncio.gather(
                self.handle_receive(websocket=websocket, close_code=close_code),
            )

        async def on_connect(self, websocket: WebSocket) -> None:
            """
            Await the websocket to accept and log the information.

            :param websocket: connected websocket
            """
            # TODO(Deepankar): To enable multiple concurrent clients,
            # Register each client - https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients
            # And move class variables to instance variable
            await websocket.accept()
            self.client_info = f'{websocket.client.host}:{websocket.client.port}'
            logger.success(
                f'Client {self.client_info} connected to stream requests via websockets'
            )

        async def handle_receive(self, websocket: WebSocket, close_code: int) -> None:
            """
            Await a message on :meth:`websocket.receive()`
            Send the message to zmqlet via :meth:`zmqlet.send_message()` and await

            :param websocket: WebSocket connection between clinet sand server.
            :param close_code: close code
            """

            def handle_route(msg: 'Message') -> 'Request':
                """
                Add route information to `message`.

                :param msg: receive message
                :return: message response with route information
                """
                msg.add_route(self.name, self._id)
                return msg.response

            try:
                while True:
                    message = await websocket.receive()
                    if message['type'] == 'websocket.receive':
                        data = await self.decode(websocket, message)
                        if data == bytes(True):
                            await asyncio.sleep(0.1)
                            continue
                        await zmqlet.send_message(
                            Message(None, Request(data), 'gateway', **vars(self.args))
                        )
                        response = await zmqlet.recv_message(callback=handle_route)
                        if self.client_encoding == 'bytes':
                            await websocket.send_bytes(response.SerializeToString())
                        else:
                            await websocket.send_json(response.json())
                    elif message['type'] == 'websocket.disconnect':
                        close_code = int(
                            message.get('code', status.WS_1000_NORMAL_CLOSURE)
                        )
                        break
            except Exception as exc:
                close_code = status.WS_1011_INTERNAL_ERROR
                logger.error(f'Got an exception in handle_receive: {exc!r}')
                raise
            finally:
                await self.on_disconnect(websocket, close_code)

        async def decode(self, websocket: WebSocket, message: Message) -> Any:
            """
            Decode the text or bytes format `message`

            :param websocket: WebSocket connection.
            :param message: Jina `Message`.
            :return: decoded message.
            """
            if 'text' in message or 'json' in message:
                self.client_encoding = 'text'

            if 'bytes' in message:
                self.client_encoding = 'bytes'

            return await super().decode(websocket, message)

        async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
            """
            Log the information when client is disconnected.

            :param websocket: disconnected websocket
            :param close_code: close code
            """
            logger.info(f'Client {self.client_info} got disconnected!')

    return app
