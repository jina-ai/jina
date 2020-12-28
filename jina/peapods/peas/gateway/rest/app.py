import json
from typing import Any

from google.protobuf.json_format import MessageToDict

from ..grpc.async_call import AsyncPrefetchCall
from .....enums import RequestType
from .....importer import ImportExtensions
from ..... import clients


def get_fastapi_app(args, logger):
    with ImportExtensions(required=True):
        from fastapi import FastAPI, Body
        from fastapi import WebSocket, WebSocketDisconnect
        from fastapi.responses import JSONResponse
        from fastapi.middleware.cors import CORSMiddleware

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

    @app.websocket(path='/stream/{mode}')
    async def stream(websocket: WebSocket, mode: str):
        if mode.upper() not in RequestType.__members__:
            return error(reason=f'unsupported mode {mode}', status_code=405)

        await websocket.accept()
        client_info = f'{websocket.client.host}:{websocket.client.port}'
        logger.success(f'Client {client_info} connected to stream requests via websockets')
        try:
            while True:
                logger.warning('server awaiting the next request')
                ws_receive = await websocket.receive()
                if 'bytes' in ws_receive:
                    request_body = ws_receive['bytes']
                elif 'text' in ws_receive:
                    request_body = json.loads(ws_receive['text'])
                    # TODO(Deepankar): convert request_body to jina.types.Request if it is text based

                # if 'data' not in request_body:
                #     await websocket.send_text('"data" field is empty')

                def gen():
                    yield request_body
                request_iterator = gen()

                # TODO(Deepankar): Using same servicer as gRPC is sub-optimal, since every `Call` creates a new zmqlet.
                # For a single stream of requests, we can have a single zmqlet to process requests
                async for response in servicer.Call(request_iterator=request_iterator, context=None):
                    await websocket.send_bytes(response.SerializeToString())
                await websocket.send_bytes(b'done')
        except WebSocketDisconnect:
            # TODO(Deepankar): For some strange reason, a different exception is raised when client disconnects.
            # websockets.exceptions.ConnectionClosedOK: code = 1000 (OK), no reason

            # While WebSocketDisconnect is a high-level exception, websockets.exceptions.ConnectionClosedOK is
            # raised by fastapi -> starlette -> uvicorn -> websockets library
            logger.info(f'client {client_info} got disconnected!')
        except Exception as e:
            logger.error(f'got an exception while streaming requests {e}')

    return app
