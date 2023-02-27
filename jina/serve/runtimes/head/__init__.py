import argparse
from abc import ABC

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from jina.enums import PollingType
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.runtimes.head.processor import HeadProcessor
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.head.request_handling import HeaderRequestHandler
from jina.serve.runtimes.helper import _get_grpc_server_options


class HeadRuntime(AsyncNewLoopRuntime, ABC):
    """
    Runtime is used in head pods. It responds to Gateway requests and sends to uses_before/uses_after and its workers
    """

    DEFAULT_POLLING = PollingType.ANY

    def __init__(
            self,
            args: argparse.Namespace,
            **kwargs,
    ):
        """Initialize grpc server for the head runtime.
        :param args: args from CLI
        :param kwargs: keyword args
        """
        self._health_servicer = health.aio.HealthServicer()
        self._processor = None
        super().__init__(args, **kwargs)

    async def async_setup(self):
        """Wait for the GRPC server to start"""
        self._processor = HeadProcessor(args=self.args,
                                        logger=self.logger,
                                        metrics_registry=self.metrics_registry,
                                        meter=self.meter,
                                        meter_provider=self.meter_provider,
                                        aio_tracing_client_interceptors=self.aio_tracing_client_interceptors(),
                                        tracing_client_interceptors=self.tracing_client_interceptor())
        self._grpc_server = grpc.aio.server(
            options=_get_grpc_server_options(self.args.grpc_server_options),
            interceptors=self.aio_tracing_server_interceptors(),
        )

        jina_pb2_grpc.add_JinaRPCServicer_to_server(self._processor, self._grpc_server)

        jina_pb2_grpc.add_JinaSingleDataRequestRPCServicer_to_server(
            self._processor, self._grpc_server
        )
        jina_pb2_grpc.add_JinaDataRequestRPCServicer_to_server(self._processor, self._grpc_server)
        jina_pb2_grpc.add_JinaDiscoverEndpointsRPCServicer_to_server(
            self._processor, self._grpc_server
        )
        jina_pb2_grpc.add_JinaInfoRPCServicer_to_server(self._processor, self._grpc_server)
        service_names = (
            jina_pb2.DESCRIPTOR.services_by_name['JinaRPC'].full_name,
            jina_pb2.DESCRIPTOR.services_by_name['JinaSingleDataRequestRPC'].full_name,
            jina_pb2.DESCRIPTOR.services_by_name['JinaDataRequestRPC'].full_name,
            jina_pb2.DESCRIPTOR.services_by_name['JinaDiscoverEndpointsRPC'].full_name,
            jina_pb2.DESCRIPTOR.services_by_name['JinaInfoRPC'].full_name,
            reflection.SERVICE_NAME,
        )
        # Mark all services as healthy.
        health_pb2_grpc.add_HealthServicer_to_server(
            self._health_servicer, self._grpc_server
        )

        reflection.enable_server_reflection(service_names, self._grpc_server)

        bind_addr = f'{self.args.host}:{self.args.port}'
        self._grpc_server.add_insecure_port(bind_addr)
        self.logger.debug(f'start listening on {bind_addr}')
        await self._grpc_server.start()
        for service in service_names:
            await self._health_servicer.set(
                service, health_pb2.HealthCheckResponse.SERVING
            )

    async def async_run_forever(self):
        """Block until the GRPC server is terminated"""
        await self._grpc_server.wait_for_termination()

    async def async_cancel(self):
        """Stop the GRPC server"""
        self.logger.debug('cancel HeadRuntime')
        self._processor.cancel_warmup_task()
        await self._grpc_server.stop(0)

    async def async_teardown(self):
        """Close the connection pool"""
        self._processor.cancel_warmup_task()
        await self._health_servicer.enter_graceful_shutdown()
        await self.async_cancel()
        await self._processor.close()
