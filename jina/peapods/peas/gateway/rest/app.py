from os import umask
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
        logger.success(f'client {client_info} connected to stream requests via websockets')
        try:
            logger.warning('before receive')
            request_body = await websocket.receive()
            logger.warning(f'after receive {request_body}')
            if 'data' not in request_body:
                logger.warning(f'before send inside not block')
                await websocket.send('"data" field is empty')
                logger.warning(f'after send inside not block')

            request_body['mode'] = RequestType.from_string(mode)
            # TODO(Deepankar): calling clients.request inside the server seems unwise. Move request out of clients?
            request_iterator = getattr(clients.request, mode)(**request_body)
            async for response in servicer.Call(request_iterator=request_iterator, context=None):
                print(response)
                await websocket.send(response)
            await websocket.send('done')
        except WebSocketDisconnect:
            logger.info(f'client {client_info} got disconnected!')

    return app
