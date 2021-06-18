import argparse
import asyncio
from typing import Any

from ....zmq import AsyncZmqlet
from ..... import __version__
from .....helper import random_identity
from .....importer import ImportExtensions
from .....logging.logger import JinaLogger
from .....types.message import Message
from .....types.request import Request


def get_fastapi_app(args: 'argparse.Namespace', logger: 'JinaLogger'):
    """
    Get the app from FastAPI as the Websocket interface.

    :param args: passed arguments.
    :param logger: Jina logger.
    :return: fastapi app
    """
    with ImportExtensions(required=True):
        from fastapi import FastAPI, WebSocket
        from starlette.endpoints import WebSocketEndpoint
        from starlette import status
        from starlette.types import Receive, Scope, Send

    app = FastAPI(
        title=args.title or 'My Jina Service',
        description=args.description
        or 'This is my awesome service. '
        'You can set `title` and `description` in your `Flow` to customize this text.',
        version=__version__,
    )

    zmqlet = AsyncZmqlet(args, logger)

    @app.on_event('shutdown')
    def _shutdown():
        zmqlet.close()

    @app.websocket(path='/')
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

        def __init__(self, scope: 'Scope', receive: 'Receive', send: 'Send') -> None:
            super().__init__(scope, receive, send)
            self._id = random_identity()
            self._client_encoding = None

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
                msg.add_route(args.name, self._id)
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
                            Message(None, Request(data), 'gateway', **vars(args))
                        )
                        response = await zmqlet.recv_message(callback=handle_route)
                        if self._client_encoding == 'bytes':
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
                self._client_encoding = 'text'

            if 'bytes' in message:
                self._client_encoding = 'bytes'

            return await super().decode(websocket, message)

        async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
            """
            Log the information when client is disconnected.

            :param websocket: disconnected websocket
            :param close_code: close code
            """
            logger.info(f'Client {self.client_info} got disconnected!')

    return app
