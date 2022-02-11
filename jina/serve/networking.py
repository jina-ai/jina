import os
import asyncio
import ipaddress
from threading import Thread
from typing import Optional, List, Dict, TYPE_CHECKING, Tuple
from urllib.parse import urlparse

import grpc
from grpc.aio import AioRpcError

from jina.logging.logger import JinaLogger
from jina.proto import jina_pb2_grpc
from jina.enums import PollingType
from jina.helper import get_or_reuse_loop
from jina.types.request import Request
from jina.types.request.control import ControlRequest
from jina.types.request.data import DataRequest

if TYPE_CHECKING:
    import kubernetes


class ReplicaList:
    """
    Maintains a list of connections to replicas and uses round robin for selecting a replica
    """

    def __init__(self):
        self._connections = []
        self._address_to_connection_idx = {}
        self._address_to_channel = {}
        self._rr_counter = 0

    def add_connection(self, address: str):
        """
        Add connection with address to the connection list
        :param address: Target address of this connection
        """
        if address not in self._address_to_connection_idx:
            try:
                parsed_address = urlparse(address)
                address = parsed_address.netloc if parsed_address.netloc else address
                use_https = parsed_address.scheme == 'https'
            except:
                use_https = False

            self._address_to_connection_idx[address] = len(self._connections)
            (
                single_data_stub,
                data_stub,
                control_stub,
                channel,
            ) = GrpcConnectionPool.create_async_channel_stub(address, https=use_https)
            self._address_to_channel[address] = channel

            self._connections.append((single_data_stub, data_stub, control_stub))

    async def remove_connection(self, address: str):
        """
        Remove connection with address from the connection list
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
            # we should handle graceful termination better, 0.5 is a rather random number here
            await self._address_to_channel[address].close(0.5)
            del self._address_to_channel[address]
            # update the address/idx mapping
            for address in self._address_to_connection_idx:
                if self._address_to_connection_idx[address] > idx_to_delete:
                    self._address_to_connection_idx[address] -= 1

            return popped_connection

        return None

    def get_next_connection(self):
        """
        Returns a connection from the list. Strategy is round robin
        :returns: A connection from the pool
        """
        try:
            connection = self._connections[self._rr_counter]
        except IndexError:
            # This can happen as a race condition while removing connections
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
    """

    class _ConnectionPoolMap:
        def __init__(self, logger: Optional[JinaLogger]):
            self._logger = logger
            # this maps deployments to shards or heads
            self._deployments: Dict[str, Dict[str, Dict[int, ReplicaList]]] = {}
            # dict stores last entity id used for a particular deployment, used for round robin
            self._access_count: Dict[str, int] = {}

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
            self, deployment: str, head: bool, entity_id: Optional[int] = None
        ) -> ReplicaList:
            if deployment in self._deployments:
                type = 'heads' if head else 'shards'
                if entity_id is None and head:
                    entity_id = 0
                return self._get_connection_list(deployment, type, entity_id)
            else:
                self._logger.debug(
                    f'Unknown deployment {deployment}, no replicas available'
                )
                return None

        def get_replicas_all_shards(self, deployment: str) -> List[ReplicaList]:
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
            self, deployment: str, type: str, entity_id: Optional[int] = None
        ) -> ReplicaList:
            try:
                if entity_id is None and len(self._deployments[deployment][type]) > 0:
                    # select a random entity
                    self._access_count[deployment] += 1
                    return self._deployments[deployment][type][
                        self._access_count[deployment]
                        % len(self._deployments[deployment][type])
                    ]
                else:
                    return self._deployments[deployment][type][entity_id]
            except KeyError:
                if (
                    entity_id is None
                    and deployment in self._deployments
                    and len(self._deployments[deployment][type])
                ):
                    # This can happen as a race condition when removing connections while accessing it
                    # In this case we don't care for the concrete entity, so retry with the first one
                    return self._get_connection_list(deployment, type, 0)
                self._logger.debug(
                    f'Did not find a connection for deployment {deployment}, type {type} and entity_id {entity_id}. There are {len(self._deployments[deployment][type]) if deployment in self._deployments else 0} available connections for this deployment and type. '
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
                connection_list = ReplicaList()
                self._deployments[deployment][type][entity_id] = connection_list

            if not self._deployments[deployment][type][entity_id].has_connection(
                address
            ):
                self._logger.debug(
                    f'Adding connection for deployment {deployment}/{type}/{entity_id} to {address}'
                )
                self._deployments[deployment][type][entity_id].add_connection(address)
            else:
                self._logger.debug(
                    f'Ignoring activation of pod, {address} already known'
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
                    f'Removing connection for deployment {deployment}/{type}/{entity_id} to {address}'
                )
                connection = await self._deployments[deployment][type][
                    entity_id
                ].remove_connection(address)
                if not self._deployments[deployment][type][entity_id].has_connections():
                    del self._deployments[deployment][type][entity_id]
                return connection
            return None

    def __init__(self, logger: Optional[JinaLogger] = None):
        self._logger = logger or JinaLogger(self.__class__.__name__)
        self._connections = self._ConnectionPoolMap(self._logger)

    def send_request(
        self,
        request: Request,
        deployment: str,
        head: bool = False,
        shard_id: Optional[int] = None,
        polling_type: PollingType = PollingType.ANY,
        endpoint: Optional[str] = None,
    ) -> List[asyncio.Task]:
        """Send a single message to target via one or all of the pooled connections, depending on polling_type. Convenience function wrapper around send_request.
        :param request: a single request to send
        :param deployment: name of the Jina deployment to send the message to
        :param head: If True it is send to the head, otherwise to the worker pods
        :param shard_id: Send to a specific shard of the deployment, ignored for polling ALL
        :param polling_type: defines if the message should be send to any or all pooled connections for the target
        :param endpoint: endpoint to target with the request
        :return: list of asyncio.Task items for each send call
        """
        return self.send_requests(
            requests=[request],
            deployment=deployment,
            head=head,
            shard_id=shard_id,
            polling_type=polling_type,
            endpoint=endpoint,
        )

    def send_requests(
        self,
        requests: List[Request],
        deployment: str,
        head: bool = False,
        shard_id: Optional[int] = None,
        polling_type: PollingType = PollingType.ANY,
        endpoint: Optional[str] = None,
    ) -> List[asyncio.Task]:
        """Send a request to target via one or all of the pooled connections, depending on polling_type

        :param requests: request (DataRequest/ControlRequest) to send
        :param deployment: name of the Jina deployment to send the request to
        :param head: If True it is send to the head, otherwise to the worker pods
        :param shard_id: Send to a specific shard of the deployment, ignored for polling ALL
        :param polling_type: defines if the request should be send to any or all pooled connections for the target
        :param endpoint: endpoint to target with the requests
        :return: list of asyncio.Task items for each send call
        """
        results = []
        connections = []
        if polling_type == PollingType.ANY:
            connection_list = self._connections.get_replicas(deployment, head, shard_id)
            if connection_list:
                connections.append(connection_list.get_next_connection())
        elif polling_type == PollingType.ALL:
            connection_lists = self._connections.get_replicas_all_shards(deployment)
            for connection_list in connection_lists:
                connections.append(connection_list.get_next_connection())
        else:
            raise ValueError(f'Unsupported polling type {polling_type}')

        for connection in connections:
            task = self._send_requests(requests, connection, endpoint)
            results.append(task)

        return results

    def send_request_once(
        self,
        request: Request,
        deployment: str,
        head: bool = False,
        shard_id: Optional[int] = None,
    ) -> asyncio.Task:
        """Send msg to target via only one of the pooled connections
        :param request: request to send
        :param deployment: name of the Jina deployment to send the message to
        :param head: If True it is send to the head, otherwise to the worker pods
        :param shard_id: Send to a specific shard of the deployment, ignored for polling ALL
        :return: asyncio.Task representing the send call
        """
        return self.send_requests_once(
            [request], deployment=deployment, head=head, shard_id=shard_id
        )

    def send_requests_once(
        self,
        requests: List[Request],
        deployment: str,
        head: bool = False,
        shard_id: Optional[int] = None,
        endpoint: Optional[str] = None,
    ) -> asyncio.Task:
        """Send a request to target via only one of the pooled connections

        :param requests: request to send
        :param deployment: name of the Jina deployment to send the request to
        :param head: If True it is send to the head, otherwise to the worker pods
        :param shard_id: Send to a specific shard of the deployment, ignored for polling ALL
        :param endpoint: endpoint to target with the requests
        :return: asyncio.Task representing the send call
        """
        replicas = self._connections.get_replicas(deployment, head, shard_id)
        if replicas:
            connection = replicas.get_next_connection()
            return self._send_requests(requests, connection, endpoint)
        else:
            self._logger.debug(
                f'No available connections for deployment {deployment} and shard {shard_id}'
            )
            return None

    def add_connection(
        self,
        deployment: str,
        address: str,
        head: Optional[bool] = False,
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

    async def remove_connection(
        self,
        deployment: str,
        address: str,
        head: Optional[bool] = False,
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

    def _send_requests(
        self, requests: List[Request], connection, endpoint: Optional[str] = None
    ) -> asyncio.Task:
        # this wraps the awaitable object from grpc as a coroutine so it can be used as a task
        # the grpc call function is not a coroutine but some _AioCall
        async def task_wrapper(requests, stubs, endpoint):
            metadata = (('endpoint', endpoint),) if endpoint else None
            for i in range(3):
                try:
                    request_type = type(requests[0])
                    if request_type == DataRequest and len(requests) == 1:

                        call_result = stubs[0].process_single_data(
                            requests[0], metadata=metadata
                        )
                        metadata, response = (
                            await call_result.trailing_metadata(),
                            await call_result,
                        )
                        return response, metadata
                    if request_type == DataRequest and len(requests) > 1:
                        call_result = stubs[1].process_data(requests, metadata=metadata)
                        metadata, response = (
                            await call_result.trailing_metadata(),
                            await call_result,
                        )
                        return response, metadata
                    elif request_type == ControlRequest:
                        call_result = stubs[2].process_control(requests[0])
                        metadata, response = (
                            await call_result.trailing_metadata(),
                            await call_result,
                        )
                        return response, metadata
                    else:
                        raise ValueError(
                            f'Unsupported request type {type(requests[0])}'
                        )
                except AioRpcError as e:
                    if e.code() != grpc.StatusCode.UNAVAILABLE:
                        raise
                    elif e.code() == grpc.StatusCode.UNAVAILABLE and i == 2:
                        self._logger.debug(f'GRPC call failed, retries exhausted')
                        raise
                    else:
                        self._logger.debug(
                            f'GRPC call failed with StatusCode.UNAVAILABLE, retry attempt {i+1}/3'
                        )

        return asyncio.create_task(task_wrapper(requests, connection, endpoint))

    @staticmethod
    def get_grpc_channel(
        address: str,
        options: Optional[list] = None,
        asyncio: Optional[bool] = False,
        https: Optional[bool] = False,
        root_certificates: Optional[str] = None,
    ) -> grpc.Channel:
        """
        Creates a grpc channel to the given address

        :param address: The address to connect to, format is <host>:<port>
        :param options: A list of options to pass to the grpc channel
        :param asyncio: If True, use the asyncio implementation of the grpc channel
        :param https: If True, use https for the grpc channel
        :param root_certificates: The path to the root certificates for https, only used if https is True

        :return: A grpc channel or an asyncio channel
        """

        secure_channel = grpc.secure_channel
        insecure_channel = grpc.insecure_channel

        if asyncio:
            secure_channel = grpc.aio.secure_channel
            insecure_channel = grpc.aio.insecure_channel

        if options is None:
            options = GrpcConnectionPool.get_default_grpc_options()

        if https:
            credentials = grpc.ssl_channel_credentials(
                root_certificates=root_certificates
            )

            return secure_channel(address, credentials, options)

        return insecure_channel(address, options)

    @staticmethod
    def activate_worker_sync(
        worker_host: str,
        worker_port: int,
        target_head: str,
        shard_id: Optional[int] = None,
    ) -> ControlRequest:
        """
        Register a given worker to a head by sending an activate request

        :param worker_host: the host address of the worker
        :param worker_port: the port of the worker
        :param target_head: address of the head to send the activate request to
        :param shard_id: id of the shard the worker belongs to
        :returns: the response request
        """
        activate_request = ControlRequest(command='ACTIVATE')
        activate_request.add_related_entity(
            'worker', worker_host, worker_port, shard_id
        )

        if os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

        return GrpcConnectionPool.send_request_sync(activate_request, target_head)

    @staticmethod
    async def activate_worker(
        worker_host: str,
        worker_port: int,
        target_head: str,
        shard_id: Optional[int] = None,
    ) -> ControlRequest:
        """
        Register a given worker to a head by sending an activate request

        :param worker_host: the host address of the worker
        :param worker_port: the port of the worker
        :param target_head: address of the head to send the activate request to
        :param shard_id: id of the shard the worker belongs to
        :returns: the response request
        """
        activate_request = ControlRequest(command='ACTIVATE')
        activate_request.add_related_entity(
            'worker', worker_host, worker_port, shard_id
        )
        return await GrpcConnectionPool.send_request_async(
            activate_request, target_head
        )

    @staticmethod
    async def deactivate_worker(
        worker_host: str,
        worker_port: int,
        target_head: str,
        shard_id: Optional[int] = None,
    ) -> ControlRequest:
        """
        Remove a given worker to a head by sending a deactivate request

        :param worker_host: the host address of the worker
        :param worker_port: the port of the worker
        :param target_head: address of the head to send the deactivate request to
        :param shard_id: id of the shard the worker belongs to
        :returns: the response request
        """
        activate_request = ControlRequest(command='DEACTIVATE')
        activate_request.add_related_entity(
            'worker', worker_host, worker_port, shard_id
        )
        return await GrpcConnectionPool.send_request_async(
            activate_request, target_head
        )

    @staticmethod
    def send_request_sync(
        request: Request,
        target: str,
        timeout=100.0,
        https=False,
        root_certificates: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> Request:
        """
        Sends a request synchronically to the target via grpc

        :param request: the request to send
        :param target: where to send the request to, like 127.0.0.1:8080
        :param timeout: timeout for the send
        :param https: if True, use https for the grpc channel
        :param root_certificates: the path to the root certificates for https, only used if https is True
        :param endpoint: endpoint to target with the request

        :returns: the response request
        """

        for i in range(3):
            try:
                with GrpcConnectionPool.get_grpc_channel(
                    target,
                    https=https,
                    root_certificates=root_certificates,
                ) as channel:
                    if type(request) == DataRequest:
                        metadata = (('endpoint', endpoint),) if endpoint else None
                        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
                        response, call = stub.process_single_data.with_call(
                            request, timeout=timeout, metadata=metadata
                        )
                    elif type(request) == ControlRequest:
                        stub = jina_pb2_grpc.JinaControlRequestRPCStub(channel)
                        response = stub.process_control(request, timeout=timeout)
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
        https: bool = False,
        root_certificates: Optional[str] = None,
    ) -> Request:
        """
        Sends a request asynchronously to the target via grpc

        :param request: the request to send
        :param target: where to send the request to, like 127.0.0.1:8080
        :param timeout: timeout for the send
        :param https: if True, use https for the grpc channel
        :param root_certificates: the path to the root certificates for https, only u

        :returns: the response request
        """

        async with GrpcConnectionPool.get_grpc_channel(
            target,
            asyncio=True,
            https=https,
            root_certificates=root_certificates,
        ) as channel:
            if type(request) == DataRequest:
                stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
                return await stub.process_single_data(request, timeout=timeout)
            elif type(request) == ControlRequest:
                stub = jina_pb2_grpc.JinaControlRequestRPCStub(channel)
                return await stub.process_control(request, timeout=timeout)

    @staticmethod
    def create_async_channel_stub(
        address,
        https=False,
        root_certificates: Optional[str] = None,
    ) -> Tuple[
        jina_pb2_grpc.JinaSingleDataRequestRPCStub,
        jina_pb2_grpc.JinaDataRequestRPCStub,
        jina_pb2_grpc.JinaControlRequestRPCStub,
        grpc.aio.Channel,
    ]:
        """
        Creates an async GRPC Channel. This channel has to be closed eventually!

        :param address: the address to create the connection to, like 127.0.0.0.1:8080
        :param https: if True, use https for the grpc channel
        :param root_certificates: the path to the root certificates for https, only u

        :returns: DataRequest/ControlRequest stubs and an async grpc channel
        """
        channel = GrpcConnectionPool.get_grpc_channel(
            address,
            asyncio=True,
            https=https,
            root_certificates=root_certificates,
        )

        return (
            jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel),
            jina_pb2_grpc.JinaDataRequestRPCStub(channel),
            jina_pb2_grpc.JinaControlRequestRPCStub(channel),
            channel,
        )


class K8sGrpcConnectionPool(GrpcConnectionPool):
    """
    Manages grpc connections to replicas in a K8s deployment.

    :param namespace: K8s namespace to operate in
    :param client: K8s client
    :param logger: the logger to use
    """

    K8S_PORT_EXPOSE = 8080
    K8S_PORT_IN = 8081
    K8S_PORT_USES_BEFORE = 8082
    K8S_PORT_USES_AFTER = 8083

    def __init__(
        self,
        namespace: str,
        client: 'kubernetes.client.CoreV1Api',
        logger: JinaLogger = None,
    ):
        super().__init__(logger=logger)

        self._namespace = namespace
        self._process_events_task = None
        self._k8s_client = client
        self._k8s_event_queue = asyncio.Queue()
        self.enabled = False

        from kubernetes import watch

        self._api_watch = watch.Watch()

        self.update_thread = Thread(target=self.run, daemon=True)

    async def _fetch_initial_state(self):
        namespaced_pods = self._k8s_client.list_namespaced_pod(self._namespace)
        for item in namespaced_pods.items:
            await self._process_item(item)

    def start(self):
        """
        Subscribe to the K8s API and watch for changes in Pods
        """
        self._loop = get_or_reuse_loop()
        self._process_events_task = asyncio.create_task(self._process_events())
        self.update_thread.start()

    async def _process_events(self):
        await self._fetch_initial_state()
        while self.enabled:
            event = await self._k8s_event_queue.get()
            await self._process_item(event)

    def run(self):
        """
        Subscribes on MODIFIED events from list_namespaced_pod AK8s PI
        """

        self.enabled = True
        while self.enabled:
            for event in self._api_watch.stream(
                self._k8s_client.list_namespaced_pod, self._namespace
            ):
                if event['type'] == 'MODIFIED':
                    asyncio.run_coroutine_threadsafe(
                        self._k8s_event_queue.put(event['object']), self._loop
                    )
                if not self.enabled:
                    break

    async def close(self):
        """
        Closes the connection pool
        """
        self.enabled = False
        if self._process_events_task:
            self._process_events_task.cancel()
        self._api_watch.stop()
        await super().close()

    @staticmethod
    def _pod_is_up(item):
        return item.status.pod_ip is not None and item.status.phase == 'Running'

    @staticmethod
    def _pod_is_ready(item):
        return item.status.container_statuses is not None and all(
            cs.ready for cs in item.status.container_statuses
        )

    async def _process_item(self, item):
        try:
            jina_deployment_name = item.metadata.labels['jina_deployment_name']

            is_head = item.metadata.labels['pod_type'].lower() == 'head'
            shard_id = (
                int(item.metadata.labels['shard_id'])
                if item.metadata.labels['shard_id'] and not is_head
                else None
            )

            is_deleted = item.metadata.deletion_timestamp is not None
            ip = item.status.pod_ip
            port = self.K8S_PORT_IN

            if (
                ip
                and port
                and not is_deleted
                and self._pod_is_up(item)
                and self._pod_is_ready(item)
            ):
                self.add_connection(
                    deployment=jina_deployment_name,
                    head=is_head,
                    address=f'{ip}:{port}',
                    shard_id=shard_id,
                )
            elif ip and port and is_deleted and self._pod_is_up(item):
                await self.remove_connection(
                    deployment=jina_deployment_name,
                    head=is_head,
                    address=f'{ip}:{port}',
                    shard_id=shard_id,
                )
        except KeyError:
            self._logger.debug(
                f'Ignoring changes to non Jina resource {item.metadata.name}'
            )
            pass

    @staticmethod
    def _extract_port(item):
        for container in item.spec.containers:
            if container.name == 'executor':
                return container.ports[0].container_port
        return None


def is_remote_local_connection(first: str, second: str):
    """
    Decides, whether ``first`` is remote host and ``second`` is localhost

    :param first: the ip or host name of the first runtime
    :param second: the ip or host name of the second runtime
    :return: True, if first is remote and second is local
    """

    try:
        first_ip = ipaddress.ip_address(first)
        first_global = first_ip.is_global
    except ValueError:
        if first == 'localhost':
            first_global = False
        else:
            first_global = True
    try:
        second_ip = ipaddress.ip_address(second)
        second_local = second_ip.is_private or second_ip.is_loopback
    except ValueError:
        if second == 'localhost':
            second_local = True
        else:
            second_local = False

    return first_global and second_local


def create_connection_pool(
    k8s_connection_pool: bool = False,
    k8s_namespace: Optional[str] = None,
    logger: Optional[JinaLogger] = None,
) -> GrpcConnectionPool:
    """
    Creates the appropriate connection pool based on parameters
    :param k8s_namespace: k8s namespace the pool will live in, None if outside K8s
    :param k8s_connection_pool: flag to indicate if K8sGrpcConnectionPool should be used, defaults to true in K8s
    :param logger: the logger to use
    :return: A connection pool object
    """
    if k8s_connection_pool and k8s_namespace:
        import kubernetes
        from kubernetes import client

        kubernetes.config.load_incluster_config()

        k8s_client = client.ApiClient()
        core_client = client.CoreV1Api(api_client=k8s_client)
        return K8sGrpcConnectionPool(
            namespace=k8s_namespace, client=core_client, logger=logger
        )
    else:
        return GrpcConnectionPool(logger=logger)


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

    return ipaddress.ip_address(hostname).is_loopback
