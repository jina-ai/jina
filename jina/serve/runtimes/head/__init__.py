import argparse
import asyncio
import contextlib
import json
import os
from abc import ABC
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from jina.enums import PollingType
from jina.excepts import InternalNetworkError
from jina.helper import get_full_version
from jina.importer import ImportExtensions
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.helper import _get_grpc_server_options
from jina.serve.runtimes.request_handlers.data_request_handler import DataRequestHandler
from jina.types.request.data import DataRequest, Response


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
        self._health_servicer = health.HealthServicer(experimental_non_blocking=True)

        super().__init__(args, **kwargs)
        if args.name is None:
            args.name = ''
        self.name = args.name
        self._deployment_name = os.getenv('JINA_DEPLOYMENT_NAME', 'worker')
        self.connection_pool = GrpcConnectionPool(
            logger=self.logger,
            compression=args.compression,
            metrics_registry=self.metrics_registry,
        )
        self._retries = self.args.retries

        if self.metrics_registry:
            with ImportExtensions(
                required=True,
                help_text='You need to install the `prometheus_client` to use the montitoring functionality of jina',
            ):
                from prometheus_client import Summary

            self._summary = (
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
            self._summary = contextlib.nullcontext()

        polling = getattr(args, 'polling', self.DEFAULT_POLLING.name)
        try:
            # try loading the polling args as json
            endpoint_polling = json.loads(polling)
            # '*' is used a wildcard and will match all endpoints, except /index, /search and explicitly defined endpoins
            default_polling = (
                PollingType.from_string(endpoint_polling['*'])
                if '*' in endpoint_polling
                else self.DEFAULT_POLLING
            )
            self._polling = self._default_polling_dict(default_polling)
            for endpoint in endpoint_polling:
                self._polling[endpoint] = PollingType(
                    endpoint_polling[endpoint]
                    if type(endpoint_polling[endpoint]) == int
                    else PollingType.from_string(endpoint_polling[endpoint])
                )
        except (ValueError, TypeError):
            # polling args is not a valid json, try interpreting as a polling enum type
            default_polling = (
                polling
                if type(polling) == PollingType
                else PollingType.from_string(polling)
            )
            self._polling = self._default_polling_dict(default_polling)

        if hasattr(args, 'connection_list') and args.connection_list:
            connection_list = json.loads(args.connection_list)
            for shard_id in connection_list:
                shard_connections = connection_list[shard_id]
                if isinstance(shard_connections, str):
                    self.connection_pool.add_connection(
                        deployment=self._deployment_name,
                        address=shard_connections,
                        shard_id=int(shard_id),
                    )
                else:
                    for connection in shard_connections:
                        self.connection_pool.add_connection(
                            deployment=self._deployment_name,
                            address=connection,
                            shard_id=int(shard_id),
                        )

        self.uses_before_address = args.uses_before_address
        self.timeout_send = args.timeout_send
        if self.timeout_send:
            self.timeout_send /= 1e3  # convert ms to seconds

        if self.uses_before_address:
            self.connection_pool.add_connection(
                deployment='uses_before', address=self.uses_before_address
            )
        self.uses_after_address = args.uses_after_address
        if self.uses_after_address:
            self.connection_pool.add_connection(
                deployment='uses_after', address=self.uses_after_address
            )
        self._reduce = not args.disable_reduce

    def _default_polling_dict(self, default_polling):
        return defaultdict(
            lambda: default_polling,
            {'/search': PollingType.ALL, '/index': PollingType.ANY},
        )

    async def async_setup(self):
        """Wait for the GRPC server to start"""
        self._grpc_server = grpc.aio.server(
            options=_get_grpc_server_options(self.args.grpc_server_options)
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
        self._grpc_server.add_insecure_port(bind_addr)
        self.logger.debug(f'start listening on {bind_addr}')
        await self._grpc_server.start()

    async def async_run_forever(self):
        """Block until the GRPC server is terminated"""
        await self._grpc_server.wait_for_termination()

    async def async_cancel(self):
        """Stop the GRPC server"""
        self.logger.debug('cancel HeadRuntime')

        await self._grpc_server.stop(0)

    async def async_teardown(self):
        """Close the connection pool"""
        self._health_servicer.enter_graceful_shutdown()
        await self.async_cancel()
        await self.connection_pool.close()

    async def process_single_data(self, request: DataRequest, context) -> DataRequest:
        """
        Process the received requests and return the result as a new request

        :param request: the data request to process
        :param context: grpc context
        :returns: the response request
        """
        return await self.process_data([request], context)

    def _handle_internalnetworkerror(self, err, context, response):
        err_code = err.code()
        if err_code == grpc.StatusCode.UNAVAILABLE:
            context.set_details(
                f'|Head: Failed to connect to worker (Executor) pod at address {err.dest_addr}. It may be down.'
            )
        elif err_code == grpc.StatusCode.DEADLINE_EXCEEDED:
            context.set_details(
                f'|Head: Connection to worker (Executor) pod at address {err.dest_addr} could be established, but timed out.'
            )
        context.set_code(err.code())
        self.logger.error(f'Error while getting responses from Pods: {err.details()}')
        if err.request_id:
            response.header.request_id = err.request_id
        return response

    async def process_data(self, requests: List[DataRequest], context) -> DataRequest:
        """
        Process the received data request and return the result as a new request

        :param requests: the data requests to process
        :param context: grpc context
        :returns: the response request
        """
        try:
            with self._summary:
                endpoint = dict(context.invocation_metadata()).get('endpoint')
                response, metadata = await self._handle_data_request(requests, endpoint)
                context.set_trailing_metadata(metadata.items())
                return response
        except InternalNetworkError as err:  # can't connect, Flow broken, interrupt the streaming through gRPC error mechanism
            return self._handle_internalnetworkerror(
                err=err, context=context, response=Response()
            )
        except (
            RuntimeError,
            Exception,
        ) as ex:  # some other error, keep streaming going just add error info
            self.logger.error(
                f'{ex!r}' + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
            requests[0].add_exception(ex, executor=None)
            context.set_trailing_metadata((('is-error', 'true'),))
            return requests[0]

    async def endpoint_discovery(self, empty, context) -> jina_pb2.EndpointsProto:
        """
        Uses the connection pool to send a discover endpoint call to the workers

        :param empty: The service expects an empty protobuf message
        :param context: grpc context
        :returns: the response request
        """
        response = jina_pb2.EndpointsProto()
        try:
            if self.uses_before_address:
                (
                    uses_before_response,
                    _,
                ) = await self.connection_pool.send_discover_endpoint(
                    deployment='uses_before', head=False
                )
                response.endpoints.extend(uses_before_response.endpoints)
            if self.uses_after_address:
                (
                    uses_after_response,
                    _,
                ) = await self.connection_pool.send_discover_endpoint(
                    deployment='uses_after', head=False
                )
                response.endpoints.extend(uses_after_response.endpoints)

            worker_response, _ = await self.connection_pool.send_discover_endpoint(
                deployment=self._deployment_name, head=False
            )
            response.endpoints.extend(worker_response.endpoints)
        except InternalNetworkError as err:  # can't connect, Flow broken, interrupt the streaming through gRPC error mechanism
            return self._handle_internalnetworkerror(
                err=err, context=context, response=response
            )

        return response

    async def _handle_data_request(
        self, requests: List[DataRequest], endpoint: Optional[str]
    ) -> Tuple[DataRequest, Dict]:
        self.logger.debug(f'recv {len(requests)} DataRequest(s)')

        DataRequestHandler.merge_routes(requests)

        uses_before_metadata = None
        if self.uses_before_address:
            (
                response,
                uses_before_metadata,
            ) = await self.connection_pool.send_requests_once(
                requests,
                deployment='uses_before',
                timeout=self.timeout_send,
                retries=self._retries,
            )
            requests = [response]

        worker_send_tasks = self.connection_pool.send_requests(
            requests=requests,
            deployment=self._deployment_name,
            polling_type=self._polling[endpoint],
            timeout=self.timeout_send,
            retries=self._retries,
        )

        worker_results = await asyncio.gather(*worker_send_tasks)

        if len(worker_results) == 0:
            raise RuntimeError(
                f'Head {self.name} did not receive a response when sending message to worker pods'
            )

        worker_results, metadata = zip(*worker_results)

        response_request = worker_results[0]
        uses_after_metadata = None
        if self.uses_after_address:
            (
                response_request,
                uses_after_metadata,
            ) = await self.connection_pool.send_requests_once(
                worker_results,
                deployment='uses_after',
                timeout=self.timeout_send,
                retries=self._retries,
            )
        elif len(worker_results) > 1 and self._reduce:
            DataRequestHandler.reduce_requests(worker_results)
        elif len(worker_results) > 1 and not self._reduce:
            # worker returned multiple responsed, but the head is configured to skip reduction
            # just concatenate the docs in this case
            response_request.data.docs = DataRequestHandler.get_docs_from_request(
                requests, field='docs'
            )

        merged_metadata = self._merge_metadata(
            metadata, uses_after_metadata, uses_before_metadata
        )

        return response_request, merged_metadata

    def _merge_metadata(self, metadata, uses_after_metadata, uses_before_metadata):
        merged_metadata = {}
        if uses_before_metadata:
            for key, value in uses_before_metadata:
                merged_metadata[key] = value
        for meta in metadata:
            for key, value in meta:
                merged_metadata[key] = value
        if uses_after_metadata:
            for key, value in uses_after_metadata:
                merged_metadata[key] = value
        return merged_metadata

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
