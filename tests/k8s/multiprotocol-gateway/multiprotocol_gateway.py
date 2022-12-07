import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection
from pydantic import BaseModel
from uvicorn import Config, Server

from jina import Gateway, __default_host__
from jina.proto import jina_pb2, jina_pb2_grpc


class DummyResponseModel(BaseModel):
    protocol: str


class MultiProtocolGateway(Gateway):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.http_port = self.ports[0]
        self.grpc_port = self.ports[1]
        self.health_servicer = health.HealthServicer(experimental_non_blocking=True)

    async def _setup_http_server(self):
        from fastapi import FastAPI

        app = FastAPI(
            title='HTTP Server',
        )

        @app.get(path='/', response_model=DummyResponseModel)
        def _get_response():
            return {'protocol': 'http'}

        self.http_server = Server(
            Config(app, host=__default_host__, port=self.http_port)
        )

    async def _setup_grpc_server(self):
        self.grpc_server = grpc.aio.server()

        jina_pb2_grpc.add_JinaRPCServicer_to_server(
            self.streamer._streamer, self.grpc_server
        )

        service_names = (
            jina_pb2.DESCRIPTOR.services_by_name['JinaRPC'].full_name,
            reflection.SERVICE_NAME,
        )
        # Mark all services as healthy.
        health_pb2_grpc.add_HealthServicer_to_server(
            self.health_servicer, self.grpc_server
        )
        for service in service_names:
            self.health_servicer.set(service, health_pb2.HealthCheckResponse.SERVING)
        reflection.enable_server_reflection(service_names, self.grpc_server)
        self.grpc_server.add_insecure_port(f'{__default_host__}:{self.grpc_port}')
        await self.grpc_server.start()

    async def setup_server(self):
        await self._setup_http_server()
        await self._setup_grpc_server()

    async def run_server(self):
        await self.http_server.serve()
        await self.grpc_server.wait_for_termination()

    async def shutdown(self):
        self.http_server.should_exit = True
        await self.grpc_server.stop(0)
        await self.http_server.shutdown()
        self.health_servicer.enter_graceful_shutdown()

    @property
    def _should_exit(self) -> bool:
        return self.http_server.should_exit
