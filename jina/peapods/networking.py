import asyncio
import ipaddress
import random
from argparse import Namespace
from threading import Thread
from typing import Optional, List, Dict, Callable, TYPE_CHECKING

import grpc

from jina.logging.logger import JinaLogger
from jina.proto import jina_pb2_grpc
from jina.types.message import Message
from .. import __default_host__, __docker_host__
from ..enums import PollingType
from ..helper import get_public_ip, get_internal_ip, get_or_reuse_loop

if TYPE_CHECKING:
    import kubernetes


class ReplicaList:
    """
    Maintains a list of connections to replicas and uses round robin for selecting a replica
    """

    def __init__(self):
        self._connections = []
        self._address_to_connection_idx = {}
        self._rr_counter = 0

    def add_connection(
        self, address: str, connection: jina_pb2_grpc.JinaDataRequestRPCStub
    ):
        """
        Add connection with address to the connection list
        :param address: Target address of this connection
        :param connection: The connection to add
        """
        if address not in self._address_to_connection_idx:
            self._address_to_connection_idx[address] = len(self._connections)
            self._connections.append(connection)

    def remove_connection(self, address: str):
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


class GrpcConnectionPool:
    """
    Manages a list of grpc connections.

    :param logger: the logger to use
    """

    class _ConnectionPoolMap:
        def __init__(self, logger: Optional[JinaLogger]):
            self._logger = logger
            # this maps pods to shards or heads
            self._pods: Dict[str, Dict[str, Dict[int, ReplicaList]]] = {}

        def add_replica(
            self,
            pod: str,
            shard_id: int,
            address: str,
            connection: Callable[[str], jina_pb2_grpc.JinaDataRequestRPCStub],
        ):
            self._add_connection(pod, shard_id, address, connection, 'shards')

        def add_head(
            self,
            pod: str,
            address: str,
            connection: Callable[[str], jina_pb2_grpc.JinaDataRequestRPCStub],
            head_id: Optional[int] = 0,
        ):  # the head_id is always 0 for now, this will change when scaling the head
            self._add_connection(pod, head_id, address, connection, 'heads')

        def get_replicas(
            self, pod: str, head: bool, entity_id: Optional[int] = None
        ) -> ReplicaList:
            if pod in self._pods:
                type = 'heads' if head else 'shards'
                if entity_id is None and head:
                    entity_id = 0
                return self._get_connection_list(pod, type, entity_id)
            else:
                return None

        def get_replicas_all_shards(self, pod: str) -> List[ReplicaList]:
            replicas = []
            if pod in self._pods:
                for shard_id in self._pods[pod]['shards']:
                    replicas.append(self._get_connection_list(pod, 'shards', shard_id))
            return replicas

        def clear(self):
            self._pods.clear()

        def _get_connection_list(
            self, pod: str, type: str, entity_id: Optional[int] = None
        ) -> ReplicaList:
            try:
                if entity_id is None:
                    # select a random entity
                    return self._pods[pod][type][
                        random.randrange(0, len(self._pods[pod][type]))
                    ]
                else:
                    return self._pods[pod][type][entity_id]
            except KeyError:
                if (
                    entity_id is None
                    and pod in self._pods
                    and len(self._pods[pod][type])
                ):
                    # This can happen as a race condition when removing connections while accessing it
                    # In this case we dont care for the concrete entity, so retry with the first one
                    return self._get_connection_list(pod, type, 0)
                return None

        def _add_pod(self, pod: str):
            if pod not in self._pods:
                self._pods[pod] = {'shards': {}, 'heads': {}}

        def _add_connection(
            self,
            pod: str,
            entity_id: int,
            address: str,
            connection: Callable[[str], jina_pb2_grpc.JinaDataRequestRPCStub],
            type: str,
        ):
            self._add_pod(pod)
            if entity_id not in self._pods[pod][type]:
                connection_list = ReplicaList()
                self._pods[pod][type][entity_id] = connection_list

            if not self._pods[pod][type][entity_id].has_connection(address):
                self._logger.debug(
                    f'Adding connection for pod {pod}/{type}/{entity_id} to {address}'
                )
                self._pods[pod][type][entity_id].add_connection(
                    address, connection(address)
                )

        def remove_head(self, pod, address, head_id: Optional[int] = 0):
            return self._remove_connection(pod, head_id, address, 'heads')

        def remove_replica(self, pod, address, shard_id: Optional[int] = 0):
            return self._remove_connection(pod, shard_id, address, 'shards')

        def _remove_connection(self, pod, entity_id, address, type):
            if pod in self._pods and entity_id in self._pods[pod][type]:
                self._logger.debug(
                    f'Removing connection for pod {pod}/{type}/{entity_id} to {address}'
                )
                connection = self._pods[pod][type][entity_id].remove_connection(address)
                if not self._pods[pod][type][entity_id].has_connections():
                    del self._pods[pod][type][entity_id]
                return connection
            return None

    def __init__(self, logger: Optional[JinaLogger] = None):
        self._logger = logger or JinaLogger(self.__class__.__name__)
        self._connections = self._ConnectionPoolMap(self._logger)

    def send_message(
        self,
        msg: Message,
        pod: str,
        head: bool,
        shard_id: Optional[int] = None,
        polling_type: PollingType = PollingType.ANY,
    ) -> List[asyncio.Task]:
        """Send msg to target via one or all of the pooled connections, depending on polling_type

        :param msg: message to send
        :param pod: name of the Jina pod to send the message to
        :param head: If True it is send to the head, otherwise to the worker peas
        :param shard_id: Send to a specific shard of the pod, ignored for polling ALL
        :param polling_type: defines if the message should be send to any or all pooled connections for the target
        :return: list of asyncio.Task items for each send call
        """
        results = []
        connections = []
        if polling_type == PollingType.ANY:
            connection_list = self._connections.get_replicas(pod, head, shard_id)
            if connection_list:
                connections.append(connection_list.get_next_connection())
        elif polling_type == PollingType.ALL:
            connection_lists = self._connections.get_replicas_all_shards(pod)
            for connection_list in connection_lists:
                connections.append(connection_list.get_next_connection())
        else:
            raise ValueError(f'Unsupported polling type {polling_type}')

        for connection in connections:
            results.append(self._send_message(msg, connection))

        return results

    def add_connection(
        self, pod: str, head: bool, address: str, shard_id: Optional[int] = None
    ):
        """
        Adds a connection for a pod to this connection pool

        :param pod: The pod the connection belongs to, like 'encoder'
        :param head: True if the connection is for a head
        :param address: Address used for the grpc connection, format is <host>:<port>
        :param shard_id: Optional parameter to indicate this connection belongs to a shard, ignored for heads
        """
        if head:
            self._connections.add_head(pod, address, self.create_connection, 0)
        else:
            if shard_id is None:
                shard_id = 0
            self._connections.add_replica(
                pod, shard_id, address, self.create_connection
            )

    def remove_connection(
        self, pod: str, head: bool, address: str, shard_id: Optional[int] = None
    ):
        """
        Removes a connection to a pod

        :param pod: The pod the connection belongs to, like 'encoder'
        :param head: True if the connection is for a head
        :param address: Address used for the grpc connection, format is <host>:<port>
        :param shard_id: Optional parameter to indicate this connection belongs to a shard, ignored for heads
        :return: The removed connection, None if it did not exist
        """
        if head:
            return self._connections.remove_head(pod, address)
        else:
            if shard_id is None:
                shard_id = 0
            return self._connections.remove_replica(pod, address, shard_id)

    def start(self):
        """
        Starts the connection pool
        """
        pass

    def close(self):
        """
        Closes the connection pool
        """
        self._connections.clear()

    def _send_message(self, msg: Message, connection) -> asyncio.Task:
        # this wraps the awaitable object from grpc as a coroutine so it can be used as a task
        # the grpc call function is not a coroutine but some _AioCall
        async def task_wrapper(new_message, stub):
            return await stub.Call(new_message)

        return asyncio.create_task(task_wrapper(msg, connection))

    @staticmethod
    def send_message_sync(msg: Message, target: str, timeout=1.0) -> Message:
        """
        Sends a message synchronizly to the target via grpc

        :param msg: the message to send
        :param target: where to send the message to, like 127.0.0.1:8080
        :param timeout: timeout for the send
        :returns: the response message
        """
        return GrpcConnectionPool.create_connection(target, is_async=False).Call(
            msg, timeout=timeout
        )

    @staticmethod
    def create_connection(
        target: str, is_async=True
    ) -> jina_pb2_grpc.JinaDataRequestRPCStub:
        """
        Creates a grpc stub to the given target address

        :param target: the adress to create the connection to, like 127.0.0.0.1:8080
        :param is_async: describes if the async version of the connction should be created, true by default
        :returns: a grpc stub
        """
        if is_async:
            channel = grpc.aio.insecure_channel(
                target,
                options=[
                    ('grpc.max_send_message_length', -1),
                    ('grpc.max_receive_message_length', -1),
                ],
            )
        else:
            channel = grpc.insecure_channel(
                target,
                options=[
                    ('grpc.max_send_message_length', -1),
                    ('grpc.max_receive_message_length', -1),
                ],
            )

        return jina_pb2_grpc.JinaDataRequestRPCStub(channel)


class K8sGrpcConnectionPool(GrpcConnectionPool):
    """
    Manages grpc connections to replicas in a K8s deployment.

    :param namespace: K8s namespace to operate in
    :param client: K8s client
    :param logger: the logger to use
    """

    def __init__(
        self,
        namespace: str,
        client: 'kubernetes.client.CoreV1Api',
        logger: JinaLogger = None,
    ):
        super().__init__(logger=logger)

        self._namespace = namespace
        self._k8s_client = client
        self._k8s_event_queue = asyncio.Queue()
        self.enabled = False

        self._fetch_initial_state()

        from kubernetes import watch

        self._api_watch = watch.Watch()

        self.update_thread = Thread(target=self.run, daemon=True)

    def _fetch_initial_state(self):
        namespaced_pods = self._k8s_client.list_namespaced_pod(self._namespace)
        for item in namespaced_pods.items:
            self._process_item(item)

    def start(self):
        """
        Subscribe to the K8s API and watch for changes in Pods
        """
        self._loop = get_or_reuse_loop()
        self._process_events_task = asyncio.create_task(self._process_events())
        self.update_thread.start()

    async def _process_events(self):
        while self.enabled:
            event = await self._k8s_event_queue.get()
            self._process_item(event)

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

    def close(self):
        """
        Closes the connection pool
        """
        self.enabled = False
        self._process_events_task.cancel()
        self._api_watch.stop()
        super().close()

    @staticmethod
    def _pod_is_up(item):
        return item.status.pod_ip is not None and item.status.phase == 'Running'

    @staticmethod
    def _pod_is_ready(item):
        return item.status.container_statuses is not None and all(
            cs.ready for cs in item.status.container_statuses
        )

    def _process_item(self, item):
        jina_pod_name = item.metadata.labels['jina_pod_name']
        is_head = item.metadata.labels['pea_type'] == 'head'
        shard_id = (
            int(item.metadata.labels['shard_id'])
            if item.metadata.labels['shard_id'] and not is_head
            else None
        )

        is_deleted = item.metadata.deletion_timestamp is not None
        ip = item.status.pod_ip
        port = self._extract_port(item)

        if (
            ip
            and port
            and not is_deleted
            and self._pod_is_up(item)
            and self._pod_is_ready(item)
        ):
            super().add_connection(
                pod=jina_pod_name,
                head=is_head,
                address=f'{ip}:{port}',
                shard_id=shard_id,
            )
        elif ip and port and is_deleted and self._pod_is_up(item):
            super().remove_connection(
                pod=jina_pod_name,
                head=is_head,
                address=f'{ip}:{port}',
                shard_id=shard_id,
            )

    @staticmethod
    def _extract_port(item):
        for container in item.spec.containers:
            if container.name == 'executor':
                return container.ports[0].container_port
        return None

    def add_connection(
        self, pod: str, head: bool, address: str, shard_id: Optional[int] = None
    ):
        """
        In K8s the connection pool is auto configured by subscribing to K8s API.
        It can not be managed manually, so add_connection is a not doing anything

        :param pod: The pod the connection belongs to, like 'encoder'
        :param head: True if the connection is for a head
        :param address: Address used for the grpc connection, format is <host>:<port>
        :param shard_id: Optional parameter to indicate this connection belongs to a shard, ignored for heads
        """
        pass

    def remove_connection(
        self, pod: str, head: bool, address: str, shard_id: Optional[int] = None
    ):
        """
        In K8s the connection pool is auto configured by subscribing to K8s API.
        It can not be managed manually, so remove_connection is a not doing anything

        :param pod: The pod the connection belongs to, like 'encoder'
        :param head: True if the connection is for a head
        :param address: Address used for the grpc connection, format is <host>:<port>
        :param shard_id: Optional parameter to indicate this connection belongs to a shard, ignored for heads
        :return: Always None as this is a Noop
        """
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


def get_connect_host(
    bind_host: str,
    bind_expose_public: bool,
    connect_args: Namespace,
) -> str:
    """
    Compute the host address for ``connect_args``

    :param bind_host: the ip for binding
    :param bind_expose_public: True, if bind socket should be exposed publicly
    :param connect_args: configuration for the host ip connection
    :return: host ip
    """
    runs_in_docker = connect_args.runs_in_docker
    # by default __default_host__ is 0.0.0.0

    # is BIND at local
    bind_local = bind_host == __default_host__

    # is CONNECT at local
    conn_local = connect_args.host == __default_host__

    # is CONNECT inside docker?
    # check if `uses` has 'docker://' or,
    # it is a remote pea managed by jinad. (all remote peas are inside docker)
    conn_docker = (
        (
            getattr(connect_args, 'uses', None) is not None
            and (
                connect_args.uses.startswith('docker://')
                or connect_args.uses.startswith('jinahub+docker://')
            )
        )
        or not conn_local
        or runs_in_docker
    )

    # is BIND & CONNECT all on the same remote?
    bind_conn_same_remote = (
        not bind_local and not conn_local and (bind_host == connect_args.host)
    )

    # pod1 in local, pod2 in local (conn_docker if pod2 in docker)
    if bind_local and conn_local:
        return __docker_host__ if conn_docker else __default_host__

    # pod1 and pod2 are remote but they are in the same host (pod2 is local w.r.t pod1)
    if bind_conn_same_remote:
        return __docker_host__ if conn_docker else __default_host__

    if bind_local and not conn_local:
        # in this case we are telling CONN (at remote) our local ip address
        if connect_args.host.startswith('localhost'):
            # this is for the "psuedo" remote tests to pass
            return __docker_host__
        return get_public_ip() if bind_expose_public else get_internal_ip()
    else:
        # in this case we (at local) need to know about remote the BIND address
        return bind_host


def create_connection_pool(
    k8s_connection_pool: bool = False,
    k8s_namespace: Optional[str] = None,
) -> GrpcConnectionPool:
    """
    Creates the appropriate connection pool based on parameters
    :param k8s_namespace: k8s namespace the pool will live in, None if outside K8s
    :param k8s_connection_pool: flag to indicate if K8sGrpcConnectionPool should be used, defaults to true in K8s
    :return: A connection pool object
    """
    if k8s_connection_pool:
        from jina.peapods.pods.k8slib.kubernetes_client import K8sClients

        k8s_clients = K8sClients()
        return K8sGrpcConnectionPool(
            namespace=k8s_namespace,
            client=k8s_clients.core_v1,
        )
    else:
        return GrpcConnectionPool()
