import argparse
import asyncio
import json
import multiprocessing
import os
import threading
from abc import ABC
from typing import Optional, Union, List, Tuple, Dict

import grpc

from ..asyncio import AsyncNewLoopRuntime
from ..request_handlers.data_request_handler import DataRequestHandler
from ...networking import create_connection_pool, K8sGrpcConnectionPool
from ....enums import PollingType
from ....proto import jina_pb2_grpc
from ....types.request.control import ControlRequest
from ....types.request.data import DataRequest


class HeadRuntime(AsyncNewLoopRuntime, ABC):
    """
    Runtime is used in head peas. It responds to Gateway requests and sends to uses_before/uses_after and its workers
    """

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
        self._pod_name = os.getenv('JINA_POD_NAME', 'worker')
        self.connection_pool = create_connection_pool(
            logger=self.logger,
            k8s_connection_pool=args.k8s_connection_pool,
            k8s_namespace=args.k8s_namespace,
        )

        # In K8s the ConnectionPool needs the information about the Jina Pod its running in
        # This is stored in the environment variable JINA_POD_NAME in all Jina K8s default templates
        if (
            type(self.connection_pool) == K8sGrpcConnectionPool
            and 'JINA_POD_NAME' not in os.environ
        ):
            raise ValueError(
                'K8s deployments need to specify the environment variable "JINA_POD_NAME"'
            )

        if hasattr(args, 'connection_list') and args.connection_list:
            connection_list = json.loads(args.connection_list)
            for shard_id in connection_list:
                self.connection_pool.add_connection(
                    pod=self._pod_name,
                    address=connection_list[shard_id],
                    shard_id=shard_id,
                )

        self.uses_before_address = args.uses_before_address

        if self.uses_before_address:
            self.connection_pool.add_connection(
                pod='uses_before', address=self.uses_before_address
            )
        self.uses_after_address = args.uses_after_address
        if self.uses_after_address:
            self.connection_pool.add_connection(
                pod='uses_after', address=self.uses_after_address
            )
        self.polling = args.polling if hasattr(args, 'polling') else PollingType.ANY

    async def async_setup(self):
        """ Wait for the GRPC server to start """
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
        bind_addr = f'0.0.0.0:{self.args.port_in}'
        self._grpc_server.add_insecure_port(bind_addr)
        self.logger.debug(f'Start listening on {bind_addr}')
        await self._grpc_server.start()

    async def async_run_forever(self):
        """Block until the GRPC server is terminated """
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
            response, metadata = await self._handle_data_request(requests)
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
                        pod=self._pod_name,
                        address=connection_string,
                        shard_id=relatedEntity.shard_id
                        if relatedEntity.HasField('shard_id')
                        else None,
                    )
            elif request.command == 'DEACTIVATE':
                for relatedEntity in request.relatedEntities:
                    connection_string = f'{relatedEntity.address}:{relatedEntity.port}'
                    await self.connection_pool.remove_connection(
                        pod=self._pod_name,
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
        self, requests: List[DataRequest]
    ) -> Tuple[DataRequest, Dict]:
        self.logger.debug(f'recv {len(requests)} DataRequest(s)')

        DataRequestHandler.merge_routes(requests)

        uses_before_metadata = None
        if self.uses_before_address:
            (
                response,
                uses_before_metadata,
            ) = await self.connection_pool.send_requests_once(
                requests, pod='uses_before'
            )
            requests = [response]
        elif len(requests) > 1:
            requests = [DataRequestHandler.reduce_requests(requests)]

        worker_send_tasks = self.connection_pool.send_requests(
            requests=requests, pod=self._pod_name, polling_type=self.polling
        )

        worker_results = await asyncio.gather(*worker_send_tasks)

        if len(worker_results) == 0:
            raise RuntimeError(
                f'Head {self.name} did not receive a response when sending message to worker peas'
            )

        worker_results, metadata = zip(*worker_results)

        response_request = worker_results[0]
        uses_after_metadata = None
        if self.uses_after_address:
            (
                response_request,
                uses_after_metadata,
            ) = await self.connection_pool.send_requests_once(
                worker_results, pod='uses_after'
            )
        elif len(worker_results) > 1:
            DataRequestHandler.reduce_requests(worker_results)

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
