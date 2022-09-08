import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from jina.helper import extend_rest_interface
from jina.proto import jina_pb2, jina_pb2_grpc

from ....gateway import BaseGateway
from ...helper import _get_grpc_server_options


class GRPCGateway(BaseGateway):
    """GRPC Gateway implementation"""

    def __init__(
        self,
        runtime,
        **kwargs,
    ):
        """Initialize the gateway
        :param runtime: runtime object
        :param kwargs: keyword args
        """
        self._runtime = runtime
        super().__init__(**kwargs)

    def get_app(self):
        """
        Initialize and return GRPC server
        :return: grpc.aio.Server
        """
        server = grpc.aio.server(
            options=_get_grpc_server_options(self.args.grpc_server_options)
        )

        jina_pb2_grpc.add_JinaRPCServicer_to_server(self.streamer._streamer, server)

        service = jina_pb2.DESCRIPTOR.services_by_name['JinaRPC'].full_name

        self._runtime._health_servicer.set(
            service, health_pb2.HealthCheckResponse.SERVING
        )

        return server
