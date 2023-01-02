from typing import Optional

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from jina import __default_host__
from jina.helper import get_full_version
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.gateway import BaseGateway
from jina.serve.runtimes.helper import _get_grpc_server_options
from jina.types.request.status import StatusMessage


class GRPCGateway(BaseGateway):
    """GRPC Gateway implementation"""

    def __init__(
        self,
        port: Optional[int] = None,
        grpc_server_options: Optional[dict] = None,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the gateway
        :param port: The port of the Gateway, which the client should connect to.
        :param grpc_server_options: Dictionary of kwargs arguments that will be passed to the grpc server as options when starting the server, example : {'grpc.max_send_message_length': -1}
        :param ssl_keyfile: the path to the key file
        :param ssl_certfile: the path to the certificate file
        :param kwargs: keyword args
        """
        super().__init__(**kwargs)
        self.port = port
        self.grpc_server_options = grpc_server_options
        self.ssl_keyfile = ssl_keyfile
        self.ssl_certfile = ssl_certfile
        self.health_servicer = health.HealthServicer(experimental_non_blocking=True)

    async def setup_server(self):
        """
        setup GRPC server
        """
        self.server = grpc.aio.server(
            options=_get_grpc_server_options(self.grpc_server_options),
            interceptors=self.grpc_tracing_server_interceptors,
        )

        jina_pb2_grpc.add_JinaRPCServicer_to_server(
            self.streamer._streamer, self.server
        )

        jina_pb2_grpc.add_JinaGatewayDryRunRPCServicer_to_server(self, self.server)
        jina_pb2_grpc.add_JinaInfoRPCServicer_to_server(self, self.server)

        service_names = (
            jina_pb2.DESCRIPTOR.services_by_name['JinaRPC'].full_name,
            jina_pb2.DESCRIPTOR.services_by_name['JinaGatewayDryRunRPC'].full_name,
            jina_pb2.DESCRIPTOR.services_by_name['JinaInfoRPC'].full_name,
            reflection.SERVICE_NAME,
        )
        # Mark all services as healthy.
        health_pb2_grpc.add_HealthServicer_to_server(self.health_servicer, self.server)

        for service in service_names:
            self.health_servicer.set(service, health_pb2.HealthCheckResponse.SERVING)
        reflection.enable_server_reflection(service_names, self.server)

        bind_addr = f'{__default_host__}:{self.port}'

        if self.ssl_keyfile and self.ssl_certfile:
            with open(self.ssl_keyfile, 'rb') as f:
                private_key = f.read()
            with open(self.ssl_certfile, 'rb') as f:
                certificate_chain = f.read()

            server_credentials = grpc.ssl_server_credentials(
                (
                    (
                        private_key,
                        certificate_chain,
                    ),
                )
            )
            self.server.add_secure_port(bind_addr, server_credentials)
        elif (
            self.ssl_keyfile != self.ssl_certfile
        ):  # if we have only ssl_keyfile and not ssl_certfile or vice versa
            raise ValueError(
                f"you can't pass a ssl_keyfile without a ssl_certfile and vice versa"
            )
        else:
            self.server.add_insecure_port(bind_addr)
        self.logger.debug(f'start server bound to {bind_addr}')
        await self.server.start()

    async def teardown(self):
        """Free other resources allocated with the server, e.g, gateway object, ..."""
        await super().teardown()
        self.health_servicer.enter_graceful_shutdown()

    async def stop_server(self):
        """
        Stop GRPC server
        """
        await self.server.stop(0)

    async def run_server(self):
        """Run GRPC server forever"""
        await self.server.wait_for_termination()

    async def dry_run(self, empty, context) -> jina_pb2.StatusProto:
        """
        Process the the call requested by having a dry run call to every Executor in the graph

        :param empty: The service expects an empty protobuf message
        :param context: grpc context
        :returns: the response request
        """
        from docarray import DocumentArray
        from jina.clients.request import request_generator
        from jina.enums import DataInputType
        from jina.serve.executors import __dry_run_endpoint__

        da = DocumentArray()

        try:
            req_iterator = request_generator(
                exec_endpoint=__dry_run_endpoint__,
                data=da,
                data_type=DataInputType.DOCUMENT,
            )
            async for _ in self.streamer.stream(request_iterator=req_iterator):
                pass
            status_message = StatusMessage()
            status_message.set_code(jina_pb2.StatusProto.SUCCESS)
            return status_message.proto
        except Exception as ex:
            status_message = StatusMessage()
            status_message.set_exception(ex)
            return status_message.proto

    async def _status(self, empty, context) -> jina_pb2.JinaInfoProto:
        """
        Process the the call requested and return the JinaInfo of the Runtime

        :param empty: The service expects an empty protobuf message
        :param context: grpc context
        :returns: the response request
        """
        infoProto = jina_pb2.JinaInfoProto()
        version, env_info = get_full_version()
        for k, v in version.items():
            infoProto.jina[k] = str(v)
        for k, v in env_info.items():
            infoProto.envs[k] = str(v)
        return infoProto
