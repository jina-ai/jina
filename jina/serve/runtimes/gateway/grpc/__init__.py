import argparse
import os

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from jina import __default_host__
from jina.excepts import PortAlreadyUsed
from jina.helper import get_full_version, is_port_free
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.bff import GatewayBFF
from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.helper import _get_grpc_server_options
from jina.types.request.status import StatusMessage

__all__ = ['GRPCGatewayRuntime']


class GRPCGatewayRuntime(GatewayRuntime):
    """Gateway Runtime for gRPC."""

    def __init__(
        self,
        args: argparse.Namespace,
        **kwargs,
    ):
        """Initialize the runtime
        :param args: args from CLI
        :param kwargs: keyword args
        """
        self._health_servicer = health.HealthServicer(experimental_non_blocking=True)
        super().__init__(args, **kwargs)

    async def async_setup(self):
        """
        The async method to setup.

        Create the gRPC server and expose the port for communication.
        """
        if not self.args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

        if not (is_port_free(__default_host__, self.args.port)):
            raise PortAlreadyUsed(f'port:{self.args.port}')

        self.server = grpc.aio.server(
            options=_get_grpc_server_options(self.args.grpc_server_options)
        )

        await self._async_setup_server()

    async def _async_setup_server(self):

        import json

        graph_description = json.loads(self.args.graph_description)
        graph_conditions = json.loads(self.args.graph_conditions)
        deployments_addresses = json.loads(self.args.deployments_addresses)
        deployments_disable_reduce = json.loads(self.args.deployments_disable_reduce)

        self.gateway_bff = GatewayBFF(
            graph_representation=graph_description,
            executor_addresses=deployments_addresses,
            graph_conditions=graph_conditions,
            deployments_disable_reduce=deployments_disable_reduce,
            timeout_send=self.timeout_send,
            retries=self.args.retries,
            compression=self.args.compression,
            runtime_name=self.name,
            prefetch=self.args.prefetch,
            logger=self.logger,
            metrics_registry=self.metrics_registry,
        )

        jina_pb2_grpc.add_JinaRPCServicer_to_server(
            self.gateway_bff._streamer, self.server
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
        health_pb2_grpc.add_HealthServicer_to_server(self._health_servicer, self.server)

        for service in service_names:
            self._health_servicer.set(service, health_pb2.HealthCheckResponse.SERVING)
        reflection.enable_server_reflection(service_names, self.server)

        bind_addr = f'{__default_host__}:{self.args.port}'

        if self.args.ssl_keyfile and self.args.ssl_certfile:
            with open(self.args.ssl_keyfile, 'rb') as f:
                private_key = f.read()
            with open(self.args.ssl_certfile, 'rb') as f:
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
            self.args.ssl_keyfile != self.args.ssl_certfile
        ):  # if we have only ssl_keyfile and not ssl_certfile or vice versa
            raise ValueError(
                f"you can't pass a ssl_keyfile without a ssl_certfile and vice versa"
            )
        else:
            self.server.add_insecure_port(bind_addr)
        self.logger.debug(f'start server bound to {bind_addr}')
        await self.server.start()

    async def async_teardown(self):
        """Close the connection pool"""
        # usually async_cancel should already have been called, but then its a noop
        # if the runtime is stopped without a sigterm (e.g. as a context manager, this can happen)
        self._health_servicer.enter_graceful_shutdown()
        await self.gateway_bff.close()
        await self.async_cancel()

    async def async_cancel(self):
        """The async method to stop server."""
        await self.server.stop(0)

    async def async_run_forever(self):
        """The async running of server."""
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
            async for _ in self.gateway_bff.stream(request_iterator=req_iterator):
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
