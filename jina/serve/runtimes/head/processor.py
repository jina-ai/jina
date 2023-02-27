import argparse
import json
import os
from collections import defaultdict
from typing import TYPE_CHECKING, AsyncIterator, List, Optional
import asyncio
import grpc

from jina.logging.logger import JinaLogger
from jina.enums import PollingType
from jina.excepts import InternalNetworkError
from jina.helper import get_full_version
from jina.proto import jina_pb2
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.head.request_handling import HeaderRequestHandler
from jina.types.request.data import DataRequest, Response

if TYPE_CHECKING:  # pragma: no cover
    from jina.types.request import Request


class HeadProcessor:
    """
    HeadProcessor class holds all the data and methods used to run the Head logic without any tie to an API
    """

    DEFAULT_POLLING = PollingType.ANY

    def __init__(self,
                 args: argparse.Namespace,
                 logger: Optional[JinaLogger],
                 metrics_registry=None,
                 meter=None,
                 meter_provider=None,
                 aio_tracing_client_interceptors=None,
                 tracing_client_interceptor=None,
                 **kwargs
                 ):
        """Initialize grpc server for the head runtime.
        :param args: args from CLI
        :param kwargs: keyword args
        """
        self.args = args
        self.logger = logger
        self.metrics_registry = metrics_registry
        self.meter = meter
        self.meter_provider = meter_provider
        if args.name is None:
            args.name = ''
        self.name = args.name
        self._deployment_name = os.getenv('JINA_DEPLOYMENT_NAME', 'worker')
        self.connection_pool = GrpcConnectionPool(
            runtime_name=self.name,
            logger=self.logger,
            compression=args.compression,
            metrics_registry=self.metrics_registry,
            meter=self.meter,
            aio_tracing_client_interceptors=aio_tracing_client_interceptors,
            tracing_client_interceptor=tracing_client_interceptor,
        )
        self._retries = self.args.retries

        polling = getattr(self.args, 'polling', self.DEFAULT_POLLING.name)
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
        self._reduce = not args.no_reduce
        self.request_handler = HeaderRequestHandler(
            logger=self.logger,
            metrics_registry=self.metrics_registry,
            meter=self.meter,
            runtime_name=self.name,
        )
        self.warmup_stop_event = asyncio.Event()
        self._warmup()

    def _warmup(self):
        self.warmup_task = asyncio.create_task(
            self.request_handler.warmup(
                connection_pool=self.connection_pool,
                stop_event=self.warmup_stop_event,
                deployment=self._deployment_name,
            )
        )

    def cancel_warmup_task(self):
        """Cancel warmup task if exists and is not completed. Cancellation is required if the Flow is being terminated before the
        task is successful or hasn't reached the max timeout.
        """
        if self.warmup_task:
            try:
                if not self.warmup_task.done():
                    self.logger.debug(f'Cancelling warmup task.')
                    self.warmup_stop_event.set() # this event is useless if simply cancel
                    self.warmup_task.cancel()
            except Exception as ex:
                self.logger.debug(f'exception during warmup task cancellation: {ex}')
                pass

    async def close(self):
        await self.connection_pool.close()

    def _default_polling_dict(self, default_polling):
        return defaultdict(
            lambda: default_polling,
            {'/search': PollingType.ALL, '/index': PollingType.ANY},
        )

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
        elif err_code == grpc.StatusCode.NOT_FOUND:
            context.set_details(
                f'|Head: Connection to worker (Executor) pod at address {err.dest_addr} could be established, but resource was not found.'
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
            endpoint = dict(context.invocation_metadata()).get('endpoint')
            self.logger.debug(f'recv {len(requests)} DataRequest(s)')
            response, metadata = await self.request_handler._handle_data_request(
                requests=requests,
                connection_pool=self.connection_pool,
                uses_before_address=self.uses_before_address,
                uses_after_address=self.uses_after_address,
                retries=self._retries,
                reduce=self._reduce,
                timeout_send=self.timeout_send,
                polling_type=self._polling[endpoint],
                deployment_name=self._deployment_name,
            )
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

    async def _status(self, empty, context) -> jina_pb2.JinaInfoProto:
        """
        Process the the call requested and return the JinaInfo of the Runtime

        :param empty: The service expects an empty protobuf message
        :param context: grpc context
        :returns: the response request
        """
        self.logger.debug('recv _status request')
        infoProto = jina_pb2.JinaInfoProto()
        version, env_info = get_full_version()
        for k, v in version.items():
            infoProto.jina[k] = str(v)
        for k, v in env_info.items():
            infoProto.envs[k] = str(v)
        return infoProto

    async def stream(
            self, request_iterator, context=None, *args, **kwargs
    ) -> AsyncIterator['Request']:
        """
        stream requests from client iterator and stream responses back.

        :param request_iterator: iterator of requests
        :param context: context of the grpc call
        :param args: positional arguments
        :param kwargs: keyword arguments
        :yield: responses to the request
        """
        async for request in request_iterator:
            yield await self.process_data([request], context)

    Call = stream
