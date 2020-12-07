import asyncio
from typing import Any

from google.protobuf.json_format import MessageToDict

from .grpc import GatewayPea
from .servicer import GRPCServicer
from ...enums import RequestType
from ...helper import configure_event_loop
from ...importer import ImportExtensions


class RESTGatewayPea(GatewayPea):
    """A :class:`BasePea`-like class for holding a HTTP Gateway.

    :class`RESTGatewayPea` is still in beta. Feature such as prefetch is not available yet.
    Unlike :class:`GatewayPea`, it does not support bi-directional streaming. Therefore, it is
    synchronous from the client perspective.
    """
    def loop_body(self):
        configure_event_loop()
        self.gateway = RESTGateway(host=self.args.host,
                                   port_expose=self.args.port_expose,
                                   servicer=GRPCServicer(self.args),
                                   logger=self.logger,
                                   proxy=self.args.proxy)
        self.set_ready()
        asyncio.get_event_loop().run_until_complete(self._loop_body())


class RESTGateway:
    def __init__(self, host, port_expose, servicer, logger, proxy) -> None:
        with ImportExtensions(required=True):
            from fastapi import FastAPI, Body
            from fastapi.encoders import jsonable_encoder
            from fastapi.responses import JSONResponse
            from fastapi.middleware.cors import CORSMiddleware

        self.host = host
        self.port_expose = port_expose
        self.servicer = servicer
        self.logger = logger
        self.is_gateway_ready = asyncio.Event()

        self.app = FastAPI(title=self.__class__.__name__)
        self.app.add_middleware(CORSMiddleware, allow_origins=['*'])

        def error(reason, status_code):
            return JSONResponse(content={'reason': reason}, status_code=status_code)

        @self.app.get('/ready')
        async def is_ready():
            return JSONResponse(status_code=200)

        @self.app.post(
            path='/api/{mode}'
        )
        async def api(mode: str, body: Any = Body(...)):
            from ...clients import python
            if mode.upper() not in RequestType.__members__:
                return error(reason=f'unsupported mode {mode}', status_code=405)

            if 'data' not in body:
                return error('"data" field is empty', 406)

            body['mode'] = RequestType.from_string(mode)
            req_iter = getattr(python.request, mode)(**body)
            results = await self.get_result_in_json(req_iter=req_iter)
            return JSONResponse(content=results[0],
                                status_code=200)

    async def get_result_in_json(self, req_iter):
        return [MessageToDict(k) async for k in self.servicer.Call(request_iterator=req_iter, context=None)]

    async def start(self):
        with ImportExtensions(required=True):
            from uvicorn import Config, Server

        self.logger.warning('you are using a REST gateway, which is still in early beta version. '
                            'advanced features such as prefetch and streaming are disabled.')

        class UvicornCustomServer(Server):
            # uvicorn only supports predefined event loops
            # hence we implement a way to serve from a custom (already running) loop
            def run(self, sockets=None):
                return asyncio.get_event_loop().create_task(self.serve(sockets=sockets))

        # change log_level for REST server debugging
        self._config = Config(app=self.app, host=self.host, port=self.port_expose, log_level='critical')
        self._server = UvicornCustomServer(config=self._config)
        self.logger.success(f'gateway (REST) is listening at: {self.host}:{self.port_expose}')
        self._server.run()
        await self.is_gateway_ready.wait()
        return self

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def close(self):
        self.is_gateway_ready.set()
        self._server.shutdown()
