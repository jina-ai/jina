import argparse
import asyncio
import json
from typing import Any, Optional, Dict

from google.protobuf.json_format import MessageToJson

from ..grpc.async_call import AsyncPrefetchCall
from ....zmq import AsyncZmqlet
from ..... import __version__
from .....clients.request import request_generator
from .....helper import get_full_version, random_identity
from .....importer import ImportExtensions
from .....logging.logger import JinaLogger
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
        from fastapi.middleware.cors import CORSMiddleware
        from starlette.endpoints import WebSocketEndpoint
        from starlette import status
        from starlette.types import Receive, Scope, Send
        from starlette.responses import StreamingResponse
        from .models import (
            JinaStatusModel,
            JinaRequestModel,
        )

    app = FastAPI(
        title=args.title or 'My Jina Service',
        description=args.description
        or 'This is my awesome service. '
        'You can set `title` and `description` in your `Flow` to customize this text.',
        version=__version__,
    )

    if args.cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
        logger.warning(
            'CORS is enabled. This service is now accessible from any website!'
        )

    zmqlet = AsyncZmqlet(args, logger)
    servicer = AsyncPrefetchCall(args, zmqlet)

    @app.on_event('shutdown')
    def _shutdown():
        zmqlet.close()

    @app.get(
        path='/status',
        summary='Get the status of Jina service',
        response_model=JinaStatusModel,
        tags=['Built-in'],
    )
    async def _status():
        """
        Get the status of this Jina service.

        This is equivalent to running `jina -vf` from command line.

        # noqa: DAR201
        """
        _info = get_full_version()
        return {
            'jina': _info[0],
            'envs': _info[1],
            'used_memory': used_memory_readable(),
        }

    @app.post(
        path='/post/{endpoint:path}',
        summary='Post a data request to some endpoint',
        response_model=JinaRequestModel,
        tags=['Built-in'],
    )
    async def post(endpoint: str, body: Optional[JinaRequestModel] = None):
        """
        Post a data request to some endpoint.

        - `endpoint`: a string that represents the executor endpoint that declared by `@requests(on=...)`

        This is equivalent to the following:

            from jina import Flow

            f = Flow().add(...)

            with f:
                f.post(endpoint, ...)

        # noqa: DAR201
        # noqa: DAR101
        """
        # The above comment is written in Markdown for better rendering in FastAPI

        bd = body.dict() if body else {'data': None}  # type: Dict
        bd['exec_endpoint'] = endpoint
        return StreamingResponse(
            result_in_stream(request_generator(**bd)), media_type='application/json'
        )

    def expose_executor_endpoint(exec_endpoint, http_path=None, **kwargs):
        """Exposing an executor endpoint to http endpoint
        :param exec_endpoint: the executor endpoint
        :param http_path: the http endpoint
        :param kwargs: kwargs accepted by FastAPI
        """

        # group flow exposed endpoints into `customized` group
        kwargs['tags'] = kwargs.get('tags', ['Customized'])

        @app.api_route(
            path=http_path or exec_endpoint, name=http_path or exec_endpoint, **kwargs
        )
        async def foo(body: JinaRequestModel):
            bd = body.dict() if body else {'data': None}
            bd['exec_endpoint'] = exec_endpoint
            return StreamingResponse(
                result_in_stream(request_generator(**bd)), media_type='application/json'
            )

    if args.endpoints_mapping:
        endpoints = json.loads(args.endpoints_mapping)  # type: Dict[str, Dict]
        for k, v in endpoints.items():
            expose_executor_endpoint(exec_endpoint=k, **v)

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
