import asyncio
import time
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Set, Tuple, Union

import grpc
from grpc.aio import AioRpcError

from jina.constants import __default_endpoint__
from jina.enums import PollingType
from jina.excepts import InternalNetworkError
from jina.importer import ImportExtensions
from jina.logging.logger import JinaLogger
from jina.proto import jina_pb2
from jina.serve.helper import format_grpc_error
from jina.serve.networking.connection_pool_map import _ConnectionPoolMap
from jina.serve.networking.connection_stub import create_async_channel_stub
from jina.serve.networking.instrumentation import (
    _NetworkingHistograms,
    _NetworkingMetrics,
)
from jina.serve.networking.replica_list import _ReplicaList
from jina.serve.networking.utils import DEFAULT_MINIMUM_RETRIES
from jina.types.request import Request

if TYPE_CHECKING:  # pragma: no cover
    import threading

    from grpc.aio._interceptor import ClientInterceptor
    from opentelemetry.instrumentation.grpc._client import (
        OpenTelemetryClientInterceptor,
    )
    from opentelemetry.metrics import Meter
    from prometheus_client import CollectorRegistry, Summary

default_endpoints_proto = jina_pb2.EndpointsProto()
default_endpoints_proto.endpoints.extend([__default_endpoint__])


class GrpcConnectionPool:
    """
    Manages a list of grpc connections.

    :param logger: the logger to use
    :param compression: The compression algorithm to be used by this GRPCConnectionPool when sending data to GRPC
    """

    K8S_PORT_USES_AFTER = 8082
    K8S_PORT_USES_BEFORE = 8081
    K8S_PORT = 8080
    K8S_PORT_MONITORING = 9090

    def __init__(
        self,
        runtime_name,
        logger: Optional[JinaLogger] = None,
        compression: Optional[str] = None,
        metrics_registry: Optional['CollectorRegistry'] = None,
        meter: Optional['Meter'] = None,
        aio_tracing_client_interceptors: Optional[Sequence['ClientInterceptor']] = None,
        tracing_client_interceptor: Optional['OpenTelemetryClientInterceptor'] = None,
    ):
        self._logger = logger or JinaLogger(self.__class__.__name__)

        self.compression = (
            getattr(grpc.Compression, compression)
            if compression
            else grpc.Compression.NoCompression
        )

        if metrics_registry:
            with ImportExtensions(
                required=True,
                help_text='You need to install the `prometheus_client` to use the montitoring functionality of jina',
            ):
                from prometheus_client import Summary

            sending_requests_time_metrics = Summary(
                'sending_request_seconds',
                'Time spent between sending a request to the Executor/Head and receiving the response',
                registry=metrics_registry,
                namespace='jina',
                labelnames=('runtime_name',),
            ).labels(runtime_name)

            received_response_bytes = Summary(
                'received_response_bytes',
                'Size in bytes of the response returned from the Head/Executor',
                registry=metrics_registry,
                namespace='jina',
                labelnames=('runtime_name',),
            ).labels(runtime_name)

            send_requests_bytes_metrics = Summary(
                'sent_request_bytes',
                'Size in bytes of the request sent to the Head/Executor',
                registry=metrics_registry,
                namespace='jina',
                labelnames=('runtime_name',),
            ).labels(runtime_name)
        else:
            sending_requests_time_metrics = None
            received_response_bytes = None
            send_requests_bytes_metrics = None

        self._metrics = _NetworkingMetrics(
            sending_requests_time_metrics,
            received_response_bytes,
            send_requests_bytes_metrics,
        )

        if meter:
            self._histograms = _NetworkingHistograms(
                sending_requests_time_metrics=meter.create_histogram(
                    name='jina_sending_request_seconds',
                    unit='s',
                    description='Time spent between sending a request to the Executor/Head and receiving the response',
                ),
                received_response_bytes=meter.create_histogram(
                    name='jina_received_response_bytes',
                    unit='By',
                    description='Size in bytes of the response returned from the Head/Executor',
                ),
                send_requests_bytes_metrics=meter.create_histogram(
                    name='jina_sent_request_bytes',
                    unit='By',
                    description='Size in bytes of the request sent to the Head/Executor',
                ),
                histogram_metric_labels={'runtime_name': runtime_name},
            )
        else:
            self._histograms = _NetworkingHistograms()

        self.aio_tracing_client_interceptors = aio_tracing_client_interceptors
        self.tracing_client_interceptor = tracing_client_interceptor
        self._connections = _ConnectionPoolMap(
            runtime_name,
            self._logger,
            self._metrics,
            self._histograms,
            self.aio_tracing_client_interceptors,
            self.tracing_client_interceptor,
        )
        self._deployment_address_map = {}

    def send_requests(
        self,
        requests: List[Request],
        deployment: str,
        head: bool = False,
        shard_id: Optional[int] = None,
        polling_type: PollingType = PollingType.ANY,
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = -1,
    ) -> List[asyncio.Task]:
        """Send a request to target via one or all of the pooled connections, depending on polling_type

        :param requests: request (DataRequest) to send
        :param deployment: name of the Jina deployment to send the request to
        :param head: If True it is send to the head, otherwise to the worker pods
        :param shard_id: Send to a specific shard of the deployment, ignored for polling ALL
        :param polling_type: defines if the request should be send to any or all pooled connections for the target
        :param endpoint: endpoint to target with the requests
        :param metadata: metadata to send with the requests
        :param timeout: timeout for sending the requests
        :param retries: number of retries per gRPC call. If <0 it defaults to max(3, num_replicas)
        :return: list of asyncio.Task items for each send call
        """
        results = []
        connections = []
        if polling_type == PollingType.ANY:
            replica_list = self._connections.get_replicas(deployment, head, shard_id)
            if replica_list:
                connections.append(replica_list)
        elif polling_type == PollingType.ALL:
            shard_replica_lists = self._connections.get_replicas_all_shards(deployment)
            for replica_list in shard_replica_lists:
                connections.append(replica_list)
        else:
            raise ValueError(f'Unsupported polling type {polling_type}')

        for replica_list in connections:
            task = self._send_requests(
                requests,
                replica_list,
                endpoint=endpoint,
                metadata=metadata,
                timeout=timeout,
                retries=retries,
            )
            results.append(task)

        return results

    def send_discover_endpoint(
        self,
        deployment: str,
        head: bool = True,
        shard_id: Optional[int] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = -1,
    ) -> Optional[asyncio.Task]:
        """Sends a discover Endpoint call to target.

        :param deployment: name of the Jina deployment to send the request to
        :param head: If True it is send to the head, otherwise to the worker pods
        :param shard_id: Send to a specific shard of the deployment, ignored for polling ALL
        :param timeout: timeout for sending the requests
        :param retries: number of retries per gRPC call. If <0 it defaults to max(3, num_replicas)
        :return: asyncio.Task items to send call
        """
        connection_list = self._connections.get_replicas(
            deployment, head, shard_id, True
        )
        if connection_list:
            return self._send_discover_endpoint(
                timeout=timeout, connection_list=connection_list, retries=retries
            )
        else:
            self._logger.debug(
                f'no available connections for deployment {deployment} and shard {shard_id}'
            )
            return None

    def send_requests_once(
        self,
        requests: List[Request],
        deployment: str,
        metadata: Optional[Dict[str, str]] = None,
        head: bool = False,
        shard_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = -1,
    ) -> Optional[asyncio.Task]:
        """Send a request to target via only one of the pooled connections

        :param requests: request to send
        :param deployment: name of the Jina deployment to send the request to
        :param metadata: metadata to send with the request
        :param head: If True it is send to the head, otherwise to the worker pods
        :param shard_id: Send to a specific shard of the deployment, ignored for polling ALL
        :param endpoint: endpoint to target with the requests
        :param timeout: timeout for sending the requests
        :param retries: number of retries per gRPC call. If <0 it defaults to max(3, num_replicas)
        :return: asyncio.Task representing the send call
        """
        replicas = self._connections.get_replicas(deployment, head, shard_id)
        if replicas:
            result = self._send_requests(
                requests,
                replicas,
                endpoint=endpoint,
                metadata=metadata,
                timeout=timeout,
                retries=retries,
            )
            return result
        else:
            self._logger.debug(
                f'no available connections for deployment {deployment} and shard {shard_id}'
            )
            return None

    def add_connection(
        self,
        deployment: str,
        address: str,
        head: bool = False,
        shard_id: Optional[int] = None,
    ):
        """
        Adds a connection for a deployment to this connection pool

        :param deployment: The deployment the connection belongs to, like 'encoder'
        :param head: True if the connection is for a head
        :param address: Address used for the grpc connection, format is <host>:<port>
        :param shard_id: Optional parameter to indicate this connection belongs to a shard, ignored for heads
        """
        if head:
            self._connections.add_head(deployment, address, 0)
        else:
            if shard_id is None:
                shard_id = 0
            self._connections.add_replica(deployment, shard_id, address)
        self._deployment_address_map[deployment] = address

    async def remove_connection(
        self,
        deployment: str,
        address: str,
        head: bool = False,
        shard_id: Optional[int] = None,
    ):
        """
        Removes a connection to a deployment

        :param deployment: The deployment the connection belongs to, like 'encoder'
        :param address: Address used for the grpc connection, format is <host>:<port>
        :param head: True if the connection is for a head
        :param shard_id: Optional parameter to indicate this connection belongs to a shard, ignored for heads
        :return: The removed connection, None if it did not exist
        """
        if head:
            return await self._connections.remove_head(deployment, address)
        else:
            if shard_id is None:
                shard_id = 0
            return await self._connections.remove_replica(deployment, address, shard_id)

    async def close(self):
        """
        Closes the connection pool
        """
        await self._connections.close()

    async def _handle_aiorpcerror(
        self,
        error: AioRpcError,
        retry_i: int = 0,
        request_id: str = '',
        tried_addresses: Set[str] = {
            ''
        },  # same deployment can have multiple addresses (replicas)
        total_num_tries: int = 1,  # number of retries + 1
        current_address: str = '',  # the specific address that was contacted during this attempt
        current_deployment: str = '',  # the specific deployment that was contacted during this attempt
        connection_list: Optional[_ReplicaList] = None,
    ) -> 'Optional[Union[AioRpcError, InternalNetworkError]]':
        # connection failures, cancelled requests, and timed out requests should be retried
        # all other cases should not be retried and will be raised immediately
        # connection failures have the code grpc.StatusCode.UNAVAILABLE
        # cancelled requests have the code grpc.StatusCode.CANCELLED
        # timed out requests have the code grpc.StatusCode.DEADLINE_EXCEEDED
        # if an Executor is down behind an API gateway, grpc.StatusCode.NOT_FOUND is returned
        # requests usually gets cancelled when the server shuts down
        # retries for cancelled requests will hit another replica in K8s
        self._logger.debug(
            f'GRPC call to {current_deployment} errored, with error {format_grpc_error(error)} and for the {retry_i + 1}th time.'
        )
        errors_to_retry = [
            grpc.StatusCode.UNAVAILABLE,
            grpc.StatusCode.DEADLINE_EXCEEDED,
            grpc.StatusCode.NOT_FOUND,
        ]
        errors_to_handle = errors_to_retry + [
            grpc.StatusCode.CANCELLED,
            grpc.StatusCode.UNKNOWN,
            grpc.StatusCode.INTERNAL,
        ]

        if error.code() not in errors_to_handle:
            return error
        elif error.code() in errors_to_retry and retry_i >= total_num_tries - 1:
            self._logger.debug(
                f'GRPC call for {current_deployment} failed, retries exhausted'
            )
            from jina.excepts import InternalNetworkError

            # after connection failure the gRPC `channel` gets stuck in a failure state for a few seconds
            # removing and re-adding the connection (stub) is faster & more reliable than just waiting
            if connection_list:
                await connection_list.reset_connection(
                    current_address, current_deployment
                )

            return InternalNetworkError(
                og_exception=error,
                request_id=request_id,
                dest_addr=tried_addresses,
                details=error.details(),
            )
        else:
            self._logger.debug(
                f'GRPC call to deployment {current_deployment} failed with error {format_grpc_error(error)}, for retry attempt {retry_i + 1}/{total_num_tries - 1}.'
                f' Trying next replica, if available.'
            )
            return None

    def _send_requests(
        self,
        requests: List[Request],
        connections: _ReplicaList,
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = -1,
    ) -> 'asyncio.Task[Union[Tuple, AioRpcError, InternalNetworkError]]':
        # this wraps the awaitable object from grpc as a coroutine so it can be used as a task
        # the grpc call function is not a coroutine but some _AioCall

        if endpoint:
            metadata = metadata or {}
            metadata['endpoint'] = endpoint

        if metadata:
            metadata = tuple(metadata.items())

        async def task_wrapper():
            tried_addresses = set()
            if retries is None or retries < 0:
                total_num_tries = (
                    max(DEFAULT_MINIMUM_RETRIES, len(connections.get_all_connections()))
                    + 1
                )
            else:
                total_num_tries = 1 + retries  # try once, then do all the retries
            for i in range(total_num_tries):
                current_connection = await connections.get_next_connection(
                    num_retries=total_num_tries
                )
                tried_addresses.add(current_connection.address)
                try:
                    return await current_connection.send_requests(
                        requests=requests,
                        metadata=metadata,
                        compression=self.compression,
                        timeout=timeout,
                    )
                except AioRpcError as e:
                    error = await self._handle_aiorpcerror(
                        error=e,
                        retry_i=i,
                        request_id=requests[0].request_id,
                        tried_addresses=tried_addresses,
                        total_num_tries=total_num_tries,
                        current_address=current_connection.address,
                        current_deployment=current_connection.deployment_name,
                        connection_list=connections,
                    )
                    if error:
                        return error
                except Exception as e:
                    return e

        return asyncio.create_task(task_wrapper())

    def _send_discover_endpoint(
        self,
        connection_list: _ReplicaList,
        timeout: Optional[float] = None,
        retries: Optional[int] = -1,
    ) -> asyncio.Task:
        # this wraps the awaitable object from grpc as a coroutine so it can be used as a task
        # the grpc call function is not a coroutine but some _AioCall
        async def task_wrapper():

            tried_addresses = set()
            if retries is None or retries < 0:
                total_num_tries = (
                    max(
                        DEFAULT_MINIMUM_RETRIES,
                        len(connection_list.get_all_connections()),
                    )
                    + 1
                )
            else:
                total_num_tries = 1 + retries  # try once, then do all the retries
            for i in range(total_num_tries):
                connection = await connection_list.get_next_connection(
                    num_retries=total_num_tries
                )
                tried_addresses.add(connection.address)
                try:
                    return await connection.send_discover_endpoint(
                        timeout=timeout,
                    )
                except AioRpcError as e:
                    error = await self._handle_aiorpcerror(
                        error=e,
                        retry_i=i,
                        tried_addresses=tried_addresses,
                        current_address=connection.address,
                        current_deployment=connection.deployment_name,
                        connection_list=connection_list,
                        total_num_tries=total_num_tries,
                    )
                    if error:
                        raise error
                except AttributeError:
                    return default_endpoints_proto, None

        return asyncio.create_task(task_wrapper())

    async def warmup(
        self,
        deployment: str,
        stop_event: 'threading.Event',
    ):
        """Executes JinaInfoRPC against the provided deployment. A single task is created for each replica connection.
        :param deployment: deployment name and the replicas that needs to be warmed up.
        :param stop_event: signal to indicate if an early termination of the task is required for graceful teardown.
        """
        self._logger.debug(f'starting warmup task for deployment {deployment}')

        async def task_wrapper(target_warmup_responses, stub):
            try:
                call_result = stub.send_info_rpc(timeout=0.5)
                await call_result
                target_warmup_responses[stub.address] = True
            except Exception:
                target_warmup_responses[stub.address] = False

        try:
            start_time = time.time()
            timeout = start_time + 60 * 5  # 5 minutes from now
            warmed_up_targets = set()
            replicas = self._get_all_replicas(deployment)

            while not stop_event.is_set():
                replica_warmup_responses = {}
                tasks = []

                for replica in replicas:
                    for stub in replica.warmup_stubs:
                        if stub.address not in warmed_up_targets:
                            tasks.append(
                                asyncio.create_task(
                                    task_wrapper(replica_warmup_responses, stub)
                                )
                            )

                await asyncio.gather(*tasks, return_exceptions=True)
                for target, response in replica_warmup_responses.items():
                    if response:
                        warmed_up_targets.add(target)

                now = time.time()
                if now > timeout or all(list(replica_warmup_responses.values())):
                    self._logger.debug(f'completed warmup task in {now - start_time}s.')
                    return

                await asyncio.sleep(0.2)
        except Exception as ex:
            self._logger.error(f'error with warmup up task: {ex}')
            return

    def _get_all_replicas(self, deployment):
        replica_set = set()
        replica_set.update(self._connections.get_replicas_all_shards(deployment))
        replica_set.add(
            self._connections.get_replicas(deployment=deployment, head=True)
        )

        return set(filter(None, replica_set))
