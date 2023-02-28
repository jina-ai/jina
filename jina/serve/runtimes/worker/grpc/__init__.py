import argparse
import asyncio
from abc import ABC

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.helper import _get_grpc_server_options
from jina.serve.runtimes.worker.processor import ExecutorProcessor


class WorkerRuntime(AsyncNewLoopRuntime, ABC):
    """Runtime procedure leveraging :class:`Grpclet` for sending DataRequests"""

    def __init__(
            self,
            args: argparse.Namespace,
            **kwargs,
    ):
        """Initialize grpc and data request handling.
        :param args: args from CLI
        :param kwargs: keyword args
        """
        self._hot_reload_task = None
        self._processor = None
        self._health_servicer = health.aio.HealthServicer()
        super().__init__(args, **kwargs)

    async def async_setup(self):
        """
        Start the WorkerRequestHandler and wait for the GRPC and Monitoring servers to start
        """
        self._processor = ExecutorProcessor(args=self.args, logger=self.logger, metrics_registry=self.metrics_registry,
                                            meter=self.meter, tracer_provider=self.tracer_provider,
                                            meter_provider=self.meter_provider, tracer=self.tracer, runtime_name=self.name)
        await self._async_setup_grpc_server()

    async def _async_setup_grpc_server(self):
        """
        Start the WorkerRequestHandler and wait for the GRPC server to start
        """

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
        self.logger.debug(f'start listening on {bind_addr}')
        self._grpc_server.add_insecure_port(bind_addr)
        await self._grpc_server.start()
        for service in service_names:
            await self._health_servicer.set(
                service, health_pb2.HealthCheckResponse.SERVING
            )

    async def async_run_forever(self):
        """Block until the GRPC server is terminated"""
        self.logger.debug(f'run grpc server forever')
        if self.args.reload:
            self._hot_reload_task = asyncio.create_task(self._processor._hot_reload())
        await self._grpc_server.wait_for_termination()

    async def async_cancel(self):
        """Stop the GRPC server"""
        self.logger.debug('cancel WorkerRuntime')
        if self._hot_reload_task is not None:
            self._hot_reload_task.cancel()
        self.logger.debug('closing the server')
        # 0.5 gives the runtime some time to complete outstanding responses
        # this should be handled better, 1.0 is a rather random number
        await self._health_servicer.enter_graceful_shutdown()
        await self._processor.close()  # allow pending requests to be processed
        await self._grpc_server.stop(1.0)
        self.logger.debug('stopped GRPC Server')

    async def async_teardown(self):
        """Close the data request handler"""
        self.logger.debug('tearing down WorkerRuntime')
        await self.async_cancel()

    async def Check(
            self, request: health_pb2.HealthCheckRequest, context
    ) -> health_pb2.HealthCheckResponse:
        """Calls the underlying HealthServicer.Check method with the same arguments
        :param request: grpc request
        :param context: grpc request context
        :returns: the grpc HealthCheckResponse
        """
        self.logger.debug(f'Receive Check request')
        return await self._health_servicer.Check(request, context)

    async def Watch(
            self, request: health_pb2.HealthCheckRequest, context
    ) -> health_pb2.HealthCheckResponse:
        """Calls the underlying HealthServicer.Watch method with the same arguments
        :param request: grpc request
        :param context: grpc request context
        :returns: the grpc HealthCheckResponse
        """
        self.logger.debug(f'Receive Watch request')
        return await self._health_servicer.Watch(request, context)
