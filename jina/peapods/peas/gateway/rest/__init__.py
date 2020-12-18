import asyncio
from typing import Any
from multiprocessing.synchronize import Event

from google.protobuf.json_format import MessageToDict

from ..grpc import GatewayPea
from ..grpc.async_call import AsyncPrefetchCall
from ..... import clients
from .....enums import RequestType
from .....importer import ImportExtensions

__all__ = ['RESTGatewayPea']


class RESTGatewayPea(GatewayPea):
    def get_fastapi_app(self):
        with ImportExtensions(required=True):
            from fastapi import FastAPI, Body
            from fastapi.responses import JSONResponse
            from fastapi.middleware.cors import CORSMiddleware

        app = FastAPI(title=self.__class__.__name__)
        app.add_middleware(CORSMiddleware, allow_origins=['*'])
        servicer = AsyncPrefetchCall(self.args)

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

    async def serve_forever(self, is_ready_event: 'Event'):
        with ImportExtensions(required=True):
            from uvicorn import Config, Server

        class UvicornCustomServer(Server):
            def run(self, sockets=None):
                # uvicorn only supports predefined event loops
                # hence we implement a way to serve from a custom (already running) loop
                asyncio.create_task(self.serve(sockets=sockets))

        # change log_level for REST server debugging
        config = Config(app=self.get_fastapi_app(),
                        host=self.args.host,
                        port=self.args.port_expose,
                        log_level='critical')
        self._server = UvicornCustomServer(config=config)
        self.logger.success(f'{self.__class__.__name__} is listening at: {self.args.host}:{self.args.port_expose}')
        self._server.run()
        is_ready_event.set()

    async def serve_terminate(self):
        await self._server.shutdown()
