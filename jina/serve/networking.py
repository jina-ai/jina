import asyncio
import contextlib
import ipaddress
import os
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import grpc
from grpc.aio import AioRpcError
from grpc_health.v1 import health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha.reflection_pb2 import ServerReflectionRequest
from grpc_reflection.v1alpha.reflection_pb2_grpc import ServerReflectionStub

from jina import __default_endpoint__
from jina.enums import PollingType
from jina.excepts import EstablishGrpcConnectionError
from jina.importer import ImportExtensions
from jina.logging.logger import JinaLogger
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.types.request import Request
from jina.types.request.data import DataRequest

TLS_PROTOCOL_SCHEMES = ['grpcs', 'https', 'wss']

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry


DEFAULT_MINIMUM_RETRIES = 3
GRACE_PERIOD_DESTROY_CONNECTION = 0.5

default_endpoints_proto = jina_pb2.EndpointsProto()
default_endpoints_proto.endpoints.extend([__default_endpoint__])


class ReplicaList:
    """
    Maintains a list of connections to replicas and uses round robin for selecting a replica
    """

    def __init__(self, summary, logger):
        self._connections = []
        self._address_to_connection_idx = {}
        self._address_to_channel = {}
        self._rr_counter = 0  # round robin counter
        self.summary = summary
        self._logger = logger
        self._destroyed_event = asyncio.Event()

    async def reset_connection(self, address: str) -> Union[grpc.aio.Channel, None]:
        """
        Removes and then re-adds a connection.
        Result is the same as calling :meth:`remove_connection` and then :meth:`add_connection`, but this allows for
        handling of race condition if multiple callers reset a connection at the same time.

        :param address: Target address of this connection
        :returns: The reset connection or None if there was no connection for the given address
        """
        self._logger.debug(f'resetting connection to {address}')

        if (
            address in self._address_to_connection_idx
            and self._address_to_connection_idx[address] is not None
        ):
            # remove connection:
            # in contrast to remove_connection(), we don't 'shorten' the data structures below, instead just set to None
            # so if someone else accesses them in the meantime, they know that they can just wait
            id_to_reset = self._address_to_connection_idx[address]
            self._address_to_connection_idx[address] = None
            connection_to_reset = self._connections[id_to_reset]
            self._connections[id_to_reset] = None
            channel_to_reset = self._address_to_channel[address]
            self._address_to_channel[address] = None
            self._destroyed_event.clear()
            await self._destroy_connection(channel_to_reset)
            self._destroyed_event.set()
            # re-add connection:
            self._address_to_connection_idx[address] = id_to_reset
            stubs, channel = self._create_connection(address)
            self._address_to_channel[address] = channel
            self._connections[id_to_reset] = stubs

            return connection_to_reset
        return None

    def add_connection(self, address: str):
        """
        Add connection with address to the connection list
        :param address: Target address of this connection
        """
        if address not in self._address_to_connection_idx:
            self._address_to_connection_idx[address] = len(self._connections)
            stubs, channel = self._create_connection(address)
            self._address_to_channel[address] = channel
            self._connections.append(stubs)

    async def remove_connection(self, address: str) -> Union[grpc.aio.Channel, None]:
        """
        Remove connection with address from the connection list

        .. warning::
            This completely removes the connection, including all dictionary keys that point to it.
            Therefore, be careful not to call this method while iterating over all connections.
            If you want to reset (remove and re-add) a connection, use :meth:`jina.serve.networking.ReplicaList.reset_connection`,
            which is safe to use in this scenario.

        :param address: Remove connection for this address
        :returns: The removed connection or None if there was not any for the given address
        """
        if address in self._address_to_connection_idx:
            self._rr_counter = (
                self._rr_counter % (len(self._connections) - 1)
                if (len(self._connections) - 1)
                else 0
            )
            idx_to_delete = self._address_to_connection_idx.pop(address)
            popped_connection = self._connections.pop(idx_to_delete)
            closing_channel = self._address_to_channel[address]
            del self._address_to_channel[address]
            await self._destroy_connection(
                closing_channel, grace=GRACE_PERIOD_DESTROY_CONNECTION
            )
            # update the address/idx mapping
            for address in self._address_to_connection_idx:
                if self._address_to_connection_idx[address] > idx_to_delete:
                    self._address_to_connection_idx[address] -= 1

            return popped_connection

        return None

    def _create_connection(self, address):
        parsed_address = urlparse(address)
        address = parsed_address.netloc if parsed_address.netloc else address
        use_tls = parsed_address.scheme in TLS_PROTOCOL_SCHEMES

        stubs, channel = GrpcConnectionPool.create_async_channel_stub(
            address, tls=use_tls, summary=self.summary
        )
        return stubs, channel

    async def _destroy_connection(self, connection, grace=0.5):
        # we should handle graceful termination better, 0.5 is a rather random number here
        await connection.close(grace)

    async def get_next_connection(self, num_retries=3):
        """
        Returns a connection from the list. Strategy is round robin
        :param num_retries: how many retries should be performed when all connections are currently unavailable
        :returns: A connection from the pool
        """
        return await self._get_next_connection(num_retries=num_retries)

    async def _get_next_connection(self, num_retries=3):
        """
        :param num_retries: how many retries should be performed when all connections are currently unavailable
        :returns: A connection from the pool
        """
        try:
            connection = None
            for i in range(len(self._connections)):
                internal_rr_counter = (self._rr_counter + i) % len(self._connections)
                connection = self._connections[internal_rr_counter]
                # connection is None if it is currently being reset. In that case, try different connection
                if connection is not None:
                    break
            all_connections_unavailable = connection is None and num_retries <= 0
            if all_connections_unavailable:
                if num_retries <= 0:
                    raise EstablishGrpcConnectionError(
                        f'Error while resetting connections {self._connections}. Connections cannot be used.'
                    )
            elif connection is None:
                # give control back to async event loop so connection resetting can be completed; then retry
                self._logger.debug(
                    f' No valid connection found, give chance for potential resetting of connection'
                )
                try:
                    await asyncio.wait_for(
                        self._destroyed_event.wait(),
                        timeout=GRACE_PERIOD_DESTROY_CONNECTION,
                    )
                finally:
                    return await self._get_next_connection(num_retries=num_retries - 1)
        except IndexError:
            # This can happen as a race condition while _removing_ connections
            self._rr_counter = 0
            connection = self._connections[self._rr_counter]
        self._rr_counter = (self._rr_counter + 1) % len(self._connections)
        return connection

    def get_all_connections(self):
        """
        Returns all available connections
        :returns: A complete list of all connections from the pool
        """
        return self._connections

    def has_connection(self, address: str) -> bool:
        """
        Checks if a connection for ip exists in the list
        :param address: The address to check
        :returns: True if a connection for the ip exists in the list
        """
        return address in self._address_to_connection_idx

    def has_connections(self) -> bool:
        """
        Checks if this contains any connection
        :returns: True if any connection is managed, False otherwise
        """
        return len(self._address_to_connection_idx) > 0

    async def close(self):
        """
        Close all connections and clean up internal state
        """
        for address in self._address_to_channel:
            await self._address_to_channel[address].close(0.5)
        self._address_to_channel.clear()
        self._address_to_connection_idx.clear()
        self._connections.clear()
        self._rr_counter = 0


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

    class ConnectionStubs:
        """
        Maintains a list of grpc stubs available for a particular connection
        """

        STUB_MAPPING = {
            'jina.JinaDataRequestRPC': jina_pb2_grpc.JinaDataRequestRPCStub,
            'jina.JinaSingleDataRequestRPC': jina_pb2_grpc.JinaSingleDataRequestRPCStub,
            'jina.JinaDiscoverEndpointsRPC': jina_pb2_grpc.JinaDiscoverEndpointsRPCStub,
            'jina.JinaRPC': jina_pb2_grpc.JinaRPCStub,
            'jina.JinaInfoRPC': jina_pb2_grpc.JinaInfoRPCStub,
        }

        def __init__(self, address, channel, summary):
            self.address = address
            self.channel = channel
            self._summary_time = summary
            self._initialized = False

        # This has to be done lazily, because the target endpoint may not be available
        # when a connection is added
        async def _init_stubs(self):
            available_services = await GrpcConnectionPool.get_available_services(
                self.channel
            )
            stubs = defaultdict(lambda: None)
            for service in available_services:
                stubs[service] = self.STUB_MAPPING[service](self.channel)
            self.data_list_stub = stubs['jina.JinaDataRequestRPC']
            self.single_data_stub = stubs['jina.JinaSingleDataRequestRPC']
            self.stream_stub = stubs['jina.JinaRPC']
            self.endpoints_discovery_stub = stubs['jina.JinaDiscoverEndpointsRPC']
            self._initialized = True

        async def send_discover_endpoint(
            self,
            timeout: Optional[float] = None,
        ) -> Tuple:
            """
            Use the endpoint discovery stub to request for the Endpoints Exposed by an Executor

            :param timeout: defines timeout for sending request

            :returns: Tuple of response and metadata about the response
            """
            if not self._initialized:
                await self._init_stubs()

            call_result = self.endpoints_discovery_stub.endpoint_discovery(
                jina_pb2.google_dot_protobuf_dot_empty__pb2.Empty(),
                timeout=timeout,
            )
            metadata, response = (
                await call_result.trailing_metadata(),
                await call_result,
            )
            return response, metadata

        async def send_requests(
            self,
            requests: List[Request],
            metadata,
            compression,
            timeout: Optional[float] = None,
        ) -> Tuple:
            """
            Send requests and uses the appropriate grpc stub for this
            Stub is chosen based on availability and type of requests

            :param requests: the requests to send
            :param metadata: the metadata to send alongside the requests
            :param compression: defines if compression should be used
            :param timeout: defines timeout for sending request

            :returns: Tuple of response and metadata about the response
            """
            if not self._initialized:
                await self._init_stubs()
            request_type = type(requests[0])
            if request_type == DataRequest and len(requests) == 1:
                if self.single_data_stub:
                    call_result = self.single_data_stub.process_single_data(
                        requests[0],
                        metadata=metadata,
                        compression=compression,
                        timeout=timeout,
                    )
                    with self._summary_time:
                        metadata, response = (
                            await call_result.trailing_metadata(),
                            await call_result,
                        )
                    return response, metadata
                elif self.stream_stub:
                    with self._summary_time:
                        async for resp in self.stream_stub.Call(
                            iter(requests), compression=compression, timeout=timeout
                        ):
                            return resp, None
            if request_type == DataRequest and len(requests) > 1:
                if self.data_list_stub:
                    call_result = self.data_list_stub.process_data(
                        requests,
                        metadata=metadata,
                        compression=compression,
                        timeout=timeout,
                    )
                    with self._summary_time:
                        metadata, response = (
                            await call_result.trailing_metadata(),
                            await call_result,
                        )
                    return response, metadata
                else:
                    raise ValueError(
                        'Can not send list of DataRequests. gRPC endpoint not available.'
                    )
            else:
                raise ValueError(f'Unsupported request type {type(requests[0])}')

    class _ConnectionPoolMap:
        def __init__(self, logger: Optional[JinaLogger], summary):
            self._logger = logger
            # this maps deployments to shards or heads
            self._deployments: Dict[str, Dict[str, Dict[int, ReplicaList]]] = {}
            # dict stores last entity id used for a particular deployment, used for round robin
            self._access_count: Dict[str, int] = {}
            self.summary = summary

            if os.name != 'nt':
                os.unsetenv('http_proxy')
                os.unsetenv('https_proxy')

        def add_replica(self, deployment: str, shard_id: int, address: str):
            self._add_connection(deployment, shard_id, address, 'shards')

        def add_head(
            self, deployment: str, address: str, head_id: Optional[int] = 0
        ):  # the head_id is always 0 for now, this will change when scaling the head
            self._add_connection(deployment, head_id, address, 'heads')

        def get_replicas(
            self,
            deployment: str,
            head: bool,
            entity_id: Optional[int] = None,
            increase_access_count: bool = True,
        ) -> ReplicaList:
            # returns all replicas of a given deployment, using a given shard
            if deployment in self._deployments:
                type_ = 'heads' if head else 'shards'
                if entity_id is None and head:
                    entity_id = 0
                return self._get_connection_list(
                    deployment, type_, entity_id, increase_access_count
                )
            else:
                self._logger.debug(
                    f'Unknown deployment {deployment}, no replicas available'
                )
                return None

        def get_replicas_all_shards(self, deployment: str) -> List[ReplicaList]:
            # returns all replicas of a given deployment, for all available shards
            # result is a list of 'shape' (num_shards, num_replicas), containing all replicas for all shards
            replicas = []
            if deployment in self._deployments:
                for shard_id in self._deployments[deployment]['shards']:
                    replicas.append(
                        self._get_connection_list(deployment, 'shards', shard_id)
                    )
            return replicas

        async def close(self):
            # Close all connections to all replicas
            for deployment in self._deployments:
                for entity_type in self._deployments[deployment]:
                    for shard_in in self._deployments[deployment][entity_type]:
                        await self._deployments[deployment][entity_type][
                            shard_in
                        ].close()
            self._deployments.clear()

        def _get_connection_list(
            self,
            deployment: str,
            type_: str,
            entity_id: Optional[int] = None,
            increase_access_count: bool = True,
        ) -> ReplicaList:
            try:
                if entity_id is None and len(self._deployments[deployment][type_]) > 0:
                    # select a random entity
                    if increase_access_count:
                        self._access_count[deployment] += 1
                    return self._deployments[deployment][type_][
                        self._access_count[deployment]
                        % len(self._deployments[deployment][type_])
                    ]
                else:
                    return self._deployments[deployment][type_][entity_id]
            except KeyError:
                if (
                    entity_id is None
                    and deployment in self._deployments
                    and len(self._deployments[deployment][type_])
                ):
                    # This can happen as a race condition when removing connections while accessing it
                    # In this case we don't care for the concrete entity, so retry with the first one
                    return self._get_connection_list(
                        deployment, type_, 0, increase_access_count
                    )
                self._logger.debug(
                    f'did not find a connection for deployment {deployment}, type {type_} and entity_id {entity_id}. There are {len(self._deployments[deployment][type_]) if deployment in self._deployments else 0} available connections for this deployment and type. '
                )
                return None

        def _add_deployment(self, deployment: str):
            if deployment not in self._deployments:
                self._deployments[deployment] = {'shards': {}, 'heads': {}}
                self._access_count[deployment] = 0

        def _add_connection(
            self,
            deployment: str,
            entity_id: int,
            address: str,
            type: str,
        ):
            self._add_deployment(deployment)
            if entity_id not in self._deployments[deployment][type]:
                connection_list = ReplicaList(self.summary, self._logger)
                self._deployments[deployment][type][entity_id] = connection_list

            if not self._deployments[deployment][type][entity_id].has_connection(
                address
            ):
                self._logger.debug(
                    f'adding connection for deployment {deployment}/{type}/{entity_id} to {address}'
                )
                self._deployments[deployment][type][entity_id].add_connection(address)
            else:
                self._logger.debug(
                    f'ignoring activation of pod, {address} already known'
                )

        async def remove_head(self, deployment, address, head_id: Optional[int] = 0):
            return await self._remove_connection(deployment, head_id, address, 'heads')

        async def remove_replica(
            self, deployment, address, shard_id: Optional[int] = 0
        ):
            return await self._remove_connection(
                deployment, shard_id, address, 'shards'
            )

        async def _remove_connection(self, deployment, entity_id, address, type):
            if (
                deployment in self._deployments
                and entity_id in self._deployments[deployment][type]
            ):
                self._logger.debug(
                    f'removing connection for deployment {deployment}/{type}/{entity_id} to {address}'
                )
                connection = await self._deployments[deployment][type][
                    entity_id
                ].remove_connection(address)
                if not self._deployments[deployment][type][entity_id].has_connections():
                    del self._deployments[deployment][type][entity_id]
                return connection
            return None

    def __init__(
        self,
        logger: Optional[JinaLogger] = None,
        compression: Optional[str] = None,
        metrics_registry: Optional['CollectorRegistry'] = None,
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

            self._summary_time = Summary(
                'sending_request_seconds',
                'Time spent between sending a request to the Pod and receiving the response',
                registry=metrics_registry,
                namespace='jina',
            ).time()
        else:
            self._summary_time = contextlib.nullcontext()
        self._connections = self._ConnectionPoolMap(self._logger, self._summary_time)
        self._deployment_address_map = {}

    def send_request(
        self,
        request: Request,
        deployment: str,
        head: bool = False,
        shard_id: Optional[int] = None,
        polling_type: PollingType = PollingType.ANY,
        endpoint: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = -1,
    ) -> List[asyncio.Task]:
        """Send a single message to target via one or all of the pooled connections, depending on polling_type. Convenience function wrapper around send_request.
        :param request: a single request to send
        :param deployment: name of the Jina deployment to send the message to
        :param head: If True it is send to the head, otherwise to the worker pods
        :param shard_id: Send to a specific shard of the deployment, ignored for polling ALL
        :param polling_type: defines if the message should be send to any or all pooled connections for the target
        :param endpoint: endpoint to target with the request
        :param timeout: timeout for sending the requests
        :param retries: number of retries per gRPC call. If <0 it defaults to max(3, num_replicas)
        :return: list of asyncio.Task items for each send call
        """
        return self.send_requests(
            requests=[request],
            deployment=deployment,
            head=head,
            shard_id=shard_id,
            polling_type=polling_type,
            endpoint=endpoint,
            timeout=timeout,
            retries=retries,
        )

    def send_requests(
        self,
        requests: List[Request],
        deployment: str,
        head: bool = False,
        shard_id: Optional[int] = None,
        polling_type: PollingType = PollingType.ANY,
        endpoint: Optional[str] = None,
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
                requests, replica_list, endpoint, timeout=timeout, retries=retries
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
    ) -> asyncio.Task:
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

    def send_request_once(
        self,
        request: Request,
        deployment: str,
        head: bool = False,
        shard_id: Optional[int] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = -1,
    ) -> asyncio.Task:
        """Send msg to target via only one of the pooled connections
        :param request: request to send
        :param deployment: name of the Jina deployment to send the message to
        :param head: If True it is send to the head, otherwise to the worker pods
        :param shard_id: Send to a specific shard of the deployment, ignored for polling ALL
        :param timeout: timeout for sending the requests
        :param retries: number of retries per gRPC call. If <0 it defaults to max(3, num_replicas)
        :return: asyncio.Task representing the send call
        """
        return self.send_requests_once(
            [request],
            deployment=deployment,
            head=head,
            shard_id=shard_id,
            timeout=timeout,
            retries=retries,
        )

    def send_requests_once(
        self,
        requests: List[Request],
        deployment: str,
        head: bool = False,
        shard_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = -1,
    ) -> asyncio.Task:
        """Send a request to target via only one of the pooled connections

        :param requests: request to send
        :param deployment: name of the Jina deployment to send the request to
        :param head: If True it is send to the head, otherwise to the worker pods
        :param shard_id: Send to a specific shard of the deployment, ignored for polling ALL
        :param endpoint: endpoint to target with the requests
        :param timeout: timeout for sending the requests
        :param retries: number of retries per gRPC call. If <0 it defaults to max(3, num_replicas)
        :return: asyncio.Task representing the send call
        """
        replicas = self._connections.get_replicas(deployment, head, shard_id)
        if replicas:
            return self._send_requests(
                requests, replicas, endpoint, timeout=timeout, retries=retries
            )
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

    def start(self):
        """
        Starts the connection pool
        """
        pass

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
        connection_list: Optional[ReplicaList] = None,
    ):
        # connection failures, cancelled requests, and timed out requests should be retried
        # all other cases should not be retried and will be raised immediately
        # connection failures have the code grpc.StatusCode.UNAVAILABLE
        # cancelled requests have the code grpc.StatusCode.CANCELLED
        # timed out requests have the code grpc.StatusCode.DEADLINE_EXCEEDED
        # requests usually gets cancelled when the server shuts down
        # retries for cancelled requests will hit another replica in K8s
        if (
            error.code() != grpc.StatusCode.UNAVAILABLE
            and error.code() != grpc.StatusCode.CANCELLED
            and error.code() != grpc.StatusCode.DEADLINE_EXCEEDED
        ):
            raise
        elif (
            error.code() == grpc.StatusCode.UNAVAILABLE
            or error.code() == grpc.StatusCode.DEADLINE_EXCEEDED
        ) and retry_i >= total_num_tries - 1:  # retries exhausted. if we land here it already failed once, therefore -1
            self._logger.debug(f'GRPC call failed, retries exhausted')
            from jina.excepts import InternalNetworkError

            # after connection failure the gRPC `channel` gets stuck in a failure state for a few seconds
            # removing and re-adding the connection (stub) is faster & more reliable than just waiting
            if connection_list:
                await connection_list.reset_connection(current_address)

            raise InternalNetworkError(
                og_exception=error,
                request_id=request_id,
                dest_addr=tried_addresses,
                details=error.details(),
            )
        else:
            self._logger.debug(
                f'GRPC call failed with code {error.code()}, retry attempt {retry_i + 1}/{total_num_tries - 1}.'
                f' Trying next replica, if available.'
            )

    def _send_requests(
        self,
        requests: List[Request],
        connections: ReplicaList,
        endpoint: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = -1,
    ) -> asyncio.Task:
        # this wraps the awaitable object from grpc as a coroutine so it can be used as a task
        # the grpc call function is not a coroutine but some _AioCall
        async def task_wrapper():
            metadata = (('endpoint', endpoint),) if endpoint else None
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
                    await self._handle_aiorpcerror(
                        error=e,
                        retry_i=i,
                        request_id=requests[0].request_id,
                        tried_addresses=tried_addresses,
                        total_num_tries=total_num_tries,
                        current_address=current_connection.address,
                        connection_list=connections,
                    )

        return asyncio.create_task(task_wrapper())

    def _send_discover_endpoint(
        self,
        connection_list: ReplicaList,
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
                    await self._handle_aiorpcerror(
                        error=e,
                        retry_i=i,
                        tried_addresses=tried_addresses,
                        current_address=connection.address,
                        connection_list=connection_list,
                        total_num_tries=total_num_tries,
                    )
                except AttributeError:
                    return default_endpoints_proto, None

        return asyncio.create_task(task_wrapper())

    @staticmethod
    def get_grpc_channel(
        address: str,
        options: Optional[list] = None,
        asyncio: bool = False,
        tls: bool = False,
        root_certificates: Optional[str] = None,
    ) -> grpc.Channel:
        """
        Creates a grpc channel to the given address

        :param address: The address to connect to, format is <host>:<port>
        :param options: A list of options to pass to the grpc channel
        :param asyncio: If True, use the asyncio implementation of the grpc channel
        :param tls: If True, use tls encryption for the grpc channel
        :param root_certificates: The path to the root certificates for tls, only used if tls is True

        :return: A grpc channel or an asyncio channel
        """

        secure_channel = grpc.secure_channel
        insecure_channel = grpc.insecure_channel

        if asyncio:
            secure_channel = grpc.aio.secure_channel
            insecure_channel = grpc.aio.insecure_channel

        if options is None:
            options = GrpcConnectionPool.get_default_grpc_options()

        if tls:
            credentials = grpc.ssl_channel_credentials(
                root_certificates=root_certificates
            )

            return secure_channel(address, credentials, options)

        return insecure_channel(address, options)

    @staticmethod
    def send_request_sync(
        request: Request,
        target: str,
        timeout=100.0,
        tls=False,
        root_certificates: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> Request:
        """
        Sends a request synchronously to the target via grpc

        :param request: the request to send
        :param target: where to send the request to, like 127.0.0.1:8080
        :param timeout: timeout for the send
        :param tls: if True, use tls encryption for the grpc channel
        :param root_certificates: the path to the root certificates for tls, only used if tls is True
        :param endpoint: endpoint to target with the request

        :returns: the response request
        """

        for i in range(3):
            try:
                with GrpcConnectionPool.get_grpc_channel(
                    target,
                    tls=tls,
                    root_certificates=root_certificates,
                ) as channel:
                    metadata = (('endpoint', endpoint),) if endpoint else None
                    stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
                    response, call = stub.process_single_data.with_call(
                        request,
                        timeout=timeout,
                        metadata=metadata,
                    )
                    return response
            except grpc.RpcError as e:
                if e.code() != grpc.StatusCode.UNAVAILABLE or i == 2:
                    raise

    @staticmethod
    def send_health_check_sync(
        target: str,
        timeout=100.0,
        tls=False,
        root_certificates: Optional[str] = None,
    ) -> health_pb2.HealthCheckResponse:
        """
        Sends a request synchronously to the target via grpc

        :param target: where to send the request to, like 127.0.0.1:8080
        :param timeout: timeout for the send
        :param tls: if True, use tls encryption for the grpc channel
        :param root_certificates: the path to the root certificates for tls, only used if tls is True

        :returns: the response health check
        """

        for i in range(3):
            try:
                with GrpcConnectionPool.get_grpc_channel(
                    target,
                    tls=tls,
                    root_certificates=root_certificates,
                ) as channel:
                    health_check_req = health_pb2.HealthCheckRequest()
                    health_check_req.service = ''
                    stub = health_pb2_grpc.HealthStub(channel)
                    return stub.Check(health_check_req, timeout=timeout)
            except grpc.RpcError as e:
                if e.code() != grpc.StatusCode.UNAVAILABLE or i == 2:
                    raise

    @staticmethod
    def send_requests_sync(
        requests: List[Request],
        target: str,
        timeout=100.0,
        tls=False,
        root_certificates: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> Request:
        """
        Sends a list of requests synchronically to the target via grpc

        :param requests: the requests to send
        :param target: where to send the request to, like 127.0.0.1:8080
        :param timeout: timeout for the send
        :param tls: if True, use tls for the grpc channel
        :param root_certificates: the path to the root certificates for tls, only used if tls is True
        :param endpoint: endpoint to target with the request

        :returns: the response request
        """

        for i in range(3):
            try:
                with GrpcConnectionPool.get_grpc_channel(
                    target,
                    tls=tls,
                    root_certificates=root_certificates,
                ) as channel:
                    metadata = (('endpoint', endpoint),) if endpoint else None
                    stub = jina_pb2_grpc.JinaDataRequestRPCStub(channel)
                    response, call = stub.process_data.with_call(
                        requests,
                        timeout=timeout,
                        metadata=metadata,
                    )
                    return response
            except grpc.RpcError as e:
                if e.code() != grpc.StatusCode.UNAVAILABLE or i == 2:
                    raise

    @staticmethod
    def get_default_grpc_options():
        """
        Returns a list of default options used for creating grpc channels.
        Documentation is here https://github.com/grpc/grpc/blob/master/include/grpc/impl/codegen/grpc_types.h
        :returns: list of tuples defining grpc parameters
        """
        return [
            ('grpc.max_send_message_length', -1),
            ('grpc.max_receive_message_length', -1),
        ]

    @staticmethod
    async def send_request_async(
        request: Request,
        target: str,
        timeout: float = 1.0,
        tls: bool = False,
        root_certificates: Optional[str] = None,
    ) -> Request:
        """
        Sends a request asynchronously to the target via grpc

        :param request: the request to send
        :param target: where to send the request to, like 127.0.0.1:8080
        :param timeout: timeout for the send
        :param tls: if True, use tls for the grpc channel
        :param root_certificates: the path to the root certificates for tls, only used if tls is True

        :returns: the response request
        """

        async with GrpcConnectionPool.get_grpc_channel(
            target,
            asyncio=True,
            tls=tls,
            root_certificates=root_certificates,
        ) as channel:
            stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
            return await stub.process_single_data(request, timeout=timeout)

    @staticmethod
    def create_async_channel_stub(
        address, tls=False, root_certificates: Optional[str] = None, summary=None
    ) -> Tuple[ConnectionStubs, grpc.aio.Channel]:
        """
        Creates an async GRPC Channel. This channel has to be closed eventually!

        :param address: the address to create the connection to, like 127.0.0.0.1:8080
        :param tls: if True, use tls for the grpc channel
        :param root_certificates: the path to the root certificates for tls, only u
        :param summary: Optional Prometheus summary object

        :returns: DataRequest stubs and an async grpc channel
        """
        channel = GrpcConnectionPool.get_grpc_channel(
            address,
            asyncio=True,
            tls=tls,
            root_certificates=root_certificates,
        )

        return (
            GrpcConnectionPool.ConnectionStubs(address, channel, summary),
            channel,
        )

    @staticmethod
    async def get_available_services(channel) -> List[str]:
        """
        Lists available services by name, exposed at target address

        :param channel: the channel to use

        :returns: List of services offered
        """
        reflection_stub = ServerReflectionStub(channel)
        response = reflection_stub.ServerReflectionInfo(
            iter([ServerReflectionRequest(list_services="")])
        )
        service_names = []
        async for res in response:
            service_names.append(
                [
                    service.name
                    for service in res.list_services_response.service
                    if service.name
                    not in {
                        'grpc.reflection.v1alpha.ServerReflection',
                        'jina.JinaGatewayDryRunRPC',
                    }
                ]
            )
        return service_names[0]


def in_docker():
    """
    Checks if the current process is running inside Docker
    :return: True if the current process is running inside Docker
    """
    path = '/proc/self/cgroup'
    if os.path.exists('/.dockerenv'):
        return True
    if os.path.isfile(path):
        with open(path) as file:
            return any('docker' in line for line in file)
    return False


def host_is_local(hostname):
    """
    Check if hostname is point to localhost
    :param hostname: host to check
    :return: True if hostname means localhost, False otherwise
    """
    import socket

    fqn = socket.getfqdn(hostname)
    if fqn in ("localhost", "0.0.0.0") or hostname == '0.0.0.0':
        return True

    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False
