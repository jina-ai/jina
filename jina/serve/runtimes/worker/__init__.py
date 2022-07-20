import argparse
import contextlib
from abc import ABC
from typing import List

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from jina.helper import get_full_version
from jina.importer import ImportExtensions
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.request_handlers.data_request_handler import DataRequestHandler
from jina.types.request.data import DataRequest


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
        self._health_servicer = health.HealthServicer(experimental_non_blocking=True)
        super().__init__(args, **kwargs)

    async def async_setup(self):
        """
        Start the DataRequestHandler and wait for the GRPC and Monitoring servers to start
        """
        if self.metrics_registry:
            with ImportExtensions(
                required=True,
                help_text='You need to install the `prometheus_client` to use the montitoring functionality of jina',
            ):
                from prometheus_client import Summary

            self._summary_time = (
                Summary(
                    'receiving_request_seconds',
                    'Time spent processing request',
                    registry=self.metrics_registry,
                    namespace='jina',
                    labelnames=('runtime_name',),
                )
                .labels(self.args.name)
                .time()
            )
        else:
            self._summary_time = contextlib.nullcontext()

        await self._async_setup_grpc_server()

    async def _async_setup_grpc_server(self):
        """
        Start the DataRequestHandler and wait for the GRPC server to start
        """

        # Keep this initialization order
        # otherwise readiness check is not valid
        # The DataRequestHandler needs to be started BEFORE the grpc server
        self._data_request_handler = DataRequestHandler(
            self.args, self.logger, self.metrics_registry
        )

        self._grpc_server = grpc.aio.server(
            options=[
                ('grpc.max_send_message_length', -1),
                ('grpc.max_receive_message_length', -1),
            ]
        )

        jina_pb2_grpc.add_JinaSingleDataRequestRPCServicer_to_server(
            self, self._grpc_server
        )
        jina_pb2_grpc.add_JinaDataRequestRPCServicer_to_server(self, self._grpc_server)

        jina_pb2_grpc.add_JinaDiscoverEndpointsRPCServicer_to_server(
            self, self._grpc_server
        )
        jina_pb2_grpc.add_JinaInfoRPCServicer_to_server(self, self._grpc_server)
        service_names = (
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

        for service in service_names:
            self._health_servicer.set(service, health_pb2.HealthCheckResponse.SERVING)
        reflection.enable_server_reflection(service_names, self._grpc_server)
        bind_addr = f'0.0.0.0:{self.args.port}'
        self.logger.debug(f'start listening on {bind_addr}')
        self._grpc_server.add_insecure_port(bind_addr)
        await self._grpc_server.start()

    async def async_run_forever(self):
        """Block until the GRPC server is terminated"""
        await self._grpc_server.wait_for_termination()

    async def async_cancel(self):
        """Stop the GRPC server"""
        self.logger.debug('cancel WorkerRuntime')

        # 0.5 gives the runtime some time to complete outstanding responses
        # this should be handled better, 1.0 is a rather random number
        await self._grpc_server.stop(1.0)
        self.logger.debug('stopped GRPC Server')

    async def async_teardown(self):
        """Close the data request handler"""
        self._health_servicer.enter_graceful_shutdown()
        await self.async_cancel()
        self._data_request_handler.close()

    async def process_single_data(self, request: DataRequest, context) -> DataRequest:
        """
        Process the received requests and return the result as a new request

        :param request: the data request to process
        :param context: grpc context
        :returns: the response request
        """
        return await self.process_data([request], context)

    async def endpoint_discovery(self, empty, context) -> jina_pb2.EndpointsProto:
        """
        Process the the call requested and return the list of Endpoints exposed by the Executor wrapped inside this Runtime

        :param empty: The service expects an empty protobuf message
        :param context: grpc context
        :returns: the response request
        """
        self.logger.debug('got an endpoint discovery request')
        endpointsProto = jina_pb2.EndpointsProto()
        endpointsProto.endpoints.extend(
            list(self._data_request_handler._executor.requests.keys())
        )
        return endpointsProto

    async def process_data(self, requests: List[DataRequest], context) -> DataRequest:
        """
        Process the received requests and return the result as a new request

        :param requests: the data requests to process
        :param context: grpc context
        :returns: the response request
        """

        with self._summary_time:
            try:
                if self.logger.debug_enabled:
                    self._log_data_request(requests[0])

                return await self._data_request_handler.handle(requests=requests)
            except (RuntimeError, Exception) as ex:
                self.logger.error(
                    f'{ex!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )

                requests[0].add_exception(ex, self._data_request_handler._executor)
                context.set_trailing_metadata((('is-error', 'true'),))
                return requests[0]

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
