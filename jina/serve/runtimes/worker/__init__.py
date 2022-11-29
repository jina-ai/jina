import argparse
import asyncio
import os
from abc import ABC
from typing import TYPE_CHECKING, List, Optional

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from jina.excepts import RuntimeTerminated
from jina.helper import get_full_version
from jina.importer import ImportExtensions
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.instrumentation import MetricsTimer
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.helper import _get_grpc_server_options
from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler
from jina.types.request.data import DataRequest

if TYPE_CHECKING:  # pragma: no cover
    from opentelemetry.propagate import Context


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
        self._health_servicer = health.aio.HealthServicer()
        super().__init__(args, **kwargs)

    async def async_setup(self):
        """
        Start the WorkerRequestHandler and wait for the GRPC and Monitoring servers to start
        """
        if self.metrics_registry:
            with ImportExtensions(
                    required=True,
                    help_text='You need to install the `prometheus_client` to use the montitoring functionality of jina',
            ):
                from prometheus_client import Counter, Summary

            self._summary = Summary(
                'receiving_request_seconds',
                'Time spent processing request',
                registry=self.metrics_registry,
                namespace='jina',
                labelnames=('runtime_name',),
            ).labels(self.args.name)

            self._failed_requests_metrics = Counter(
                'failed_requests',
                'Number of failed requests',
                registry=self.metrics_registry,
                namespace='jina',
                labelnames=('runtime_name',),
            ).labels(self.args.name)

            self._successful_requests_metrics = Counter(
                'successful_requests',
                'Number of successful requests',
                registry=self.metrics_registry,
                namespace='jina',
                labelnames=('runtime_name',),
            ).labels(self.args.name)

        else:
            self._summary = None
            self._failed_requests_metrics = None
            self._successful_requests_metrics = None

        if self.meter:
            self._receiving_request_seconds = self.meter.create_histogram(
                name='jina_receiving_request_seconds',
                description='Time spent processing request',
            )
            self._failed_requests_counter = self.meter.create_counter(
                name='jina_failed_requests',
                description='Number of failed requests',
            )

            self._successful_requests_counter = self.meter.create_counter(
                name='jina_successful_requests',
                description='Number of successful requests',
            )
        else:
            self._receiving_request_seconds = None
            self._failed_requests_counter = None
            self._successful_requests_counter = None
        self._metric_attributes = {'runtime_name': self.args.name}

        # Keep this initialization order
        # otherwise readiness check is not valid
        # The WorkerRequestHandler needs to be started BEFORE the grpc server
        self._request_handler = WorkerRequestHandler(
            args=self.args,
            logger=self.logger,
            metrics_registry=self.metrics_registry,
            tracer_provider=self.tracer_provider,
            meter_provider=self.meter_provider,
            deployment_name=self.name.split('/')[0],
        )
        await self._async_setup_grpc_server()

    async def _async_setup_grpc_server(self):
        """
        Start the WorkerRequestHandler and wait for the GRPC server to start
        """

        self._grpc_server = grpc.aio.server(
            options=_get_grpc_server_options(self.args.grpc_server_options),
            interceptors=self.aio_tracing_server_interceptors(),
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
            await self._health_servicer.set(
                service, health_pb2.HealthCheckResponse.SERVING
            )
        reflection.enable_server_reflection(service_names, self._grpc_server)
        bind_addr = f'{self.args.host}:{self.args.port}'
        self.logger.debug(f'start listening on {bind_addr}')
        self._grpc_server.add_insecure_port(bind_addr)
        await self._grpc_server.start()

    async def _hot_reload(self):
        import inspect
        executor_file = inspect.getfile(self._request_handler._executor.__class__)
        watched_files = set([executor_file] + (self.args.py_modules or []))
        executor_base_path = os.path.dirname(os.path.abspath(executor_file))
        extra_paths = [os.path.join(path, name) for path, subdirs, files in os.walk(executor_base_path) for name in files]
        extra_python_paths = list(filter(lambda x: x.endswith('.py'), extra_paths))
        for extra_python_file in extra_python_paths:
            watched_files.add(extra_python_file)

        with ImportExtensions(
                required=True,
                logger=self.logger,
                help_text='''hot reload requires watchfiles dependency to be installed. You can do `pip install 
                watchfiles''',
        ):
            from watchfiles import awatch

        async for changes in awatch(*watched_files):
            changed_files = [changed_file for _, changed_file in changes]
            self.logger.info(
                f'detected changes in: {changed_files}. Refreshing the Executor'
            )
            self._request_handler._refresh_executor(changed_files)

    async def async_run_forever(self):
        """Block until the GRPC server is terminated"""
        if self.args.reload:
            self._hot_reload_task = asyncio.create_task(self._hot_reload())
        await self._grpc_server.wait_for_termination()

    async def async_cancel(self):
        """Stop the GRPC server"""
        self.logger.debug('cancel WorkerRuntime')
        if self._hot_reload_task is not None:
            self._hot_reload_task.cancel()
        # 0.5 gives the runtime some time to complete outstanding responses
        # this should be handled better, 1.0 is a rather random number
        await self._grpc_server.stop(1.0)
        self.logger.debug('stopped GRPC Server')

    async def async_teardown(self):
        """Close the data request handler"""
        await self._health_servicer.enter_graceful_shutdown()
        await self.async_cancel()
        self._request_handler.close()

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
        endpoints_proto = jina_pb2.EndpointsProto()
        endpoints_proto.endpoints.extend(
            list(self._request_handler._executor.requests.keys())
        )
        return endpoints_proto

    def _extract_tracing_context(
            self, metadata: grpc.aio.Metadata
    ) -> Optional['Context']:
        if self.tracer:
            from opentelemetry.propagate import extract

            context = extract(dict(metadata))
            return context

        return None

    async def process_data(self, requests: List[DataRequest], context) -> DataRequest:
        """
        Process the received requests and return the result as a new request

        :param requests: the data requests to process
        :param context: grpc context
        :returns: the response request
        """

        with MetricsTimer(
                self._summary, self._receiving_request_seconds, self._metric_attributes
        ):
            try:
                if self.logger.debug_enabled:
                    self._log_data_request(requests[0])

                tracing_context = self._extract_tracing_context(
                    context.invocation_metadata()
                )
                result = await self._request_handler.handle(
                    requests=requests, tracing_context=tracing_context
                )
                if self._successful_requests_metrics:
                    self._successful_requests_metrics.inc()
                if self._successful_requests_counter:
                    self._successful_requests_counter.add(
                        1, attributes=self._metric_attributes
                    )
                return result
            except (RuntimeError, Exception) as ex:
                self.logger.error(
                    f'{ex!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )

                requests[0].add_exception(ex, self._request_handler._executor)
                context.set_trailing_metadata((('is-error', 'true'),))
                if self._failed_requests_metrics:
                    self._failed_requests_metrics.inc()
                if self._failed_requests_counter:
                    self._failed_requests_counter.add(
                        1, attributes=self._metric_attributes
                    )

                if (
                        self.args.exit_on_exceptions
                        and type(ex).__name__ in self.args.exit_on_exceptions
                ):
                    self.logger.info('Exiting because of "--exit-on-exceptions".')
                    raise RuntimeTerminated

                return requests[0]

    async def _status(self, empty, context) -> jina_pb2.JinaInfoProto:
        """
        Process the the call requested and return the JinaInfo of the Runtime

        :param empty: The service expects an empty protobuf message
        :param context: grpc context
        :returns: the response request
        """
        info_proto = jina_pb2.JinaInfoProto()
        version, env_info = get_full_version()
        for k, v in version.items():
            info_proto.jina[k] = str(v)
        for k, v in env_info.items():
            info_proto.envs[k] = str(v)
        return info_proto
