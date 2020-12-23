from typing import Any

from google.protobuf.json_format import MessageToDict

from ..grpc.async_call import AsyncPrefetchCall
from .....enums import RequestType
from .....importer import ImportExtensions
from ..... import clients


def get_fastapi_app(args):
    with ImportExtensions(required=True):
        from fastapi import FastAPI, Body
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
        req_iter = getattr(clients.request, mode)(**body)
        results = await get_result_in_json(req_iter=req_iter)
        return JSONResponse(content=results[0], status_code=200)

    async def get_result_in_json(req_iter):
        return [MessageToDict(k) async for k in servicer.Call(request_iterator=req_iter, context=None)]

    return app
