import argparse
import asyncio
import json
import multiprocessing
import os
import threading
from abc import ABC
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union

import grpc

from jina.enums import PollingType
from jina.proto import jina_pb2_grpc
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.request_handlers.data_request_handler import DataRequestHandler
from jina.types.request.control import ControlRequest
from jina.types.request.data import DataRequest


class HeadRuntime(AsyncNewLoopRuntime, ABC):
    """
    Runtime is used in head pods. It responds to Gateway requests and sends to uses_before/uses_after and its workers
    """

    DEFAULT_POLLING = PollingType.ANY

    def __init__(
        self,
        args: argparse.Namespace,
        cancel_event: Optional[
            Union['asyncio.Event', 'multiprocessing.Event', 'threading.Event']
        ] = None,
        **kwargs,
    ):
        """Initialize grpc server for the head runtime.
        :param args: args from CLI
        :param cancel_event: the cancel event used to wait for canceling
        :param kwargs: keyword args
        """
        super().__init__(args, cancel_event, **kwargs)

        if args.name is None:
            args.name = ''
        self.name = args.name
        self._deployment_name = os.getenv('JINA_DEPLOYMENT_NAME', 'worker')
        self.connection_pool = GrpcConnectionPool(
            logger=self.logger, compression=args.compression
        )
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
            options=[
                ('grpc.max_send_message_length', -1),
                ('grpc.max_receive_message_length', -1),
            ]
        )

        jina_pb2_grpc.add_JinaSingleDataRequestRPCServicer_to_server(
            self, self._grpc_server
        )
        jina_pb2_grpc.add_JinaDataRequestRPCServicer_to_server(self, self._grpc_server)
        jina_pb2_grpc.add_JinaControlRequestRPCServicer_to_server(
            self, self._grpc_server
        )
        bind_addr = f'0.0.0.0:{self.args.port}'
        self._grpc_server.add_insecure_port(bind_addr)
        self.logger.debug(f'Start listening on {bind_addr}')
        await self._grpc_server.start()

    async def async_run_forever(self):
        """Block until the GRPC server is terminated"""
        self.connection_pool.start()
        await self._grpc_server.wait_for_termination()

    async def async_cancel(self):
        """Stop the GRPC server"""
        self.logger.debug('Cancel HeadRuntime')

        await self._grpc_server.stop(0)

    async def async_teardown(self):
        """Close the connection pool"""
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

    async def process_data(self, requests: List[DataRequest], context) -> DataRequest:
        """
        Process the received data request and return the result as a new request

        :param requests: the data requests to process
        :param context: grpc context
        :returns: the response request
        """
        try:
            endpoint = dict(context.invocation_metadata()).get('endpoint')
            response, metadata = await self._handle_data_request(requests, endpoint)
            context.set_trailing_metadata(metadata.items())
            return response
        except (RuntimeError, Exception) as ex:
            self.logger.error(
                f'{ex!r}' + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
            raise

    async def process_control(self, request: ControlRequest, *args) -> ControlRequest:
        """
        Process the received control request and return the input request

        :param request: the data request to process
        :param args: additional arguments in the grpc call, ignored
        :returns: the input request
        """
        try:
            if self.logger.debug_enabled:
                self._log_control_request(request)

            if request.command == 'ACTIVATE':

                for relatedEntity in request.relatedEntities:
                    connection_string = f'{relatedEntity.address}:{relatedEntity.port}'

                    self.connection_pool.add_connection(
                        deployment=self._deployment_name,
                        address=connection_string,
                        shard_id=relatedEntity.shard_id
                        if relatedEntity.HasField('shard_id')
                        else None,
                    )
            elif request.command == 'DEACTIVATE':
                for relatedEntity in request.relatedEntities:
                    connection_string = f'{relatedEntity.address}:{relatedEntity.port}'
                    await self.connection_pool.remove_connection(
                        deployment=self._deployment_name,
                        address=connection_string,
                        shard_id=relatedEntity.shard_id,
                    )
            return request
        except (RuntimeError, Exception) as ex:
            self.logger.error(
                f'{ex!r}' + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
            raise

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
                requests, deployment='uses_before'
            )
            requests = [response]

        worker_send_tasks = self.connection_pool.send_requests(
            requests=requests,
            deployment=self._deployment_name,
            polling_type=self._polling[endpoint],
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
                worker_results, deployment='uses_after'
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
