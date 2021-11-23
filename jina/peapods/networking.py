import asyncio
import ipaddress
import random
from threading import Thread
from typing import Optional, List, Dict, TYPE_CHECKING, Tuple

import grpc
from grpc.aio import AioRpcError

from jina.logging.logger import JinaLogger
from jina.proto import jina_pb2_grpc
from jina.types.message import Message
from ..enums import PollingType
from ..helper import get_or_reuse_loop
from ..types.message.common import ControlMessage

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
            self._address_to_connection_idx[address] = len(self._connections)
            stub, channel = GrpcConnectionPool.create_async_channel_stub(address)
            self._address_to_channel[address] = channel

            self._connections.append(stub)

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
            await self._address_to_channel[address].close(None)
            del self._address_to_channel[address]

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

    async def close(self):
        """
        Close all connections and clean up internal state
        """
        for address in self._address_to_channel:
            await self._address_to_channel[address].close(None)
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
            # this maps pods to shards or heads
            self._pods: Dict[str, Dict[str, Dict[int, ReplicaList]]] = {}

        def add_replica(self, pod: str, shard_id: int, address: str):
            self._add_connection(pod, shard_id, address, 'shards')

        def add_head(
            self, pod: str, address: str, head_id: Optional[int] = 0
        ):  # the head_id is always 0 for now, this will change when scaling the head
            self._add_connection(pod, head_id, address, 'heads')

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

        async def close(self):
            # Close all connections to all replicas
            for pod in self._pods:
                for entity_type in self._pods[pod]:
                    for shard_in in self._pods[pod][entity_type]:
                        await self._pods[pod][entity_type][shard_in].close()
            self._pods.clear()

        def _get_connection_list(
            self, pod: str, type: str, entity_id: Optional[int] = None
        ) -> ReplicaList:
            try:
                if entity_id is None and len(self._pods[pod][type]) > 0:
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
                self._pods[pod][type][entity_id].add_connection(address)

        async def remove_head(self, pod, address, head_id: Optional[int] = 0):
            return await self._remove_connection(pod, head_id, address, 'heads')

        async def remove_replica(self, pod, address, shard_id: Optional[int] = 0):
            return await self._remove_connection(pod, shard_id, address, 'shards')

        async def _remove_connection(self, pod, entity_id, address, type):
            if pod in self._pods and entity_id in self._pods[pod][type]:
                self._logger.debug(
                    f'Removing connection for pod {pod}/{type}/{entity_id} to {address}'
                )
                connection = await self._pods[pod][type][entity_id].remove_connection(
                    address
                )
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
        head: bool = False,
        shard_id: Optional[int] = None,
        polling_type: PollingType = PollingType.ANY,
    ) -> List[asyncio.Task]:
        """Send a single message to target via one or all of the pooled connections, depending on polling_type. Convinience function wrapper around send_messages

        :param msg: a single message to send
        :param pod: name of the Jina pod to send the message to
        :param head: If True it is send to the head, otherwise to the worker peas
        :param shard_id: Send to a specific shard of the pod, ignored for polling ALL
        :param polling_type: defines if the message should be send to any or all pooled connections for the target
        :return: list of asyncio.Task items for each send call
        """
        return self.send_messages(
            messages=[msg],
            pod=pod,
            head=head,
            shard_id=shard_id,
            polling_type=polling_type,
        )

    def send_messages(
        self,
        messages: List[Message],
        pod: str,
        head: bool = False,
        shard_id: Optional[int] = None,
        polling_type: PollingType = PollingType.ANY,
    ) -> List[asyncio.Task]:
        """Send messages to target via one or all of the pooled connections, depending on polling_type

        :param messages: list of messages to send
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
            task = self._send_messages(messages, connection)
            results.append(task)

        return results

    def send_message_once(
        self,
        msg: Message,
        pod: str,
        head: bool = False,
        shard_id: Optional[int] = None,
    ) -> asyncio.Task:
        """Send msg to target via only one of the pooled connections

        :param msg: message to send
        :param pod: name of the Jina pod to send the message to
        :param head: If True it is send to the head, otherwise to the worker peas
        :param shard_id: Send to a specific shard of the pod, ignored for polling ALL
        :return: asyncio.Task representing the send call
        """
        return self.send_messages_once([msg], pod=pod, head=head, shard_id=shard_id)

    def send_messages_once(
        self,
        messages: List[Message],
        pod: str,
        head: bool = False,
        shard_id: Optional[int] = None,
    ) -> asyncio.Task:
        """Send messages to target via only one of the pooled connections

        :param messages: list of messages to send
        :param pod: name of the Jina pod to send the message to
        :param head: If True it is send to the head, otherwise to the worker peas
        :param shard_id: Send to a specific shard of the pod, ignored for polling ALL
        :return: asyncio.Task representing the send call
        """
        connection = self._connections.get_replicas(
            pod, head, shard_id
        ).get_next_connection()

        return self._send_messages(messages, connection)

    def add_connection(
        self,
        pod: str,
        address: str,
        head: Optional[bool] = False,
        shard_id: Optional[int] = None,
    ):
        """
        Adds a connection for a pod to this connection pool

        :param pod: The pod the connection belongs to, like 'encoder'
        :param head: True if the connection is for a head
        :param address: Address used for the grpc connection, format is <host>:<port>
        :param shard_id: Optional parameter to indicate this connection belongs to a shard, ignored for heads
        """
        if head:
            self._connections.add_head(pod, address, 0)
        else:
            if shard_id is None:
                shard_id = 0
            self._connections.add_replica(pod, shard_id, address)

    async def remove_connection(
        self,
        pod: str,
        address: str,
        head: Optional[bool] = False,
        shard_id: Optional[int] = None,
    ):
        """
        Removes a connection to a pod

        :param pod: The pod the connection belongs to, like 'encoder'
        :param address: Address used for the grpc connection, format is <host>:<port>
        :param head: True if the connection is for a head
        :param shard_id: Optional parameter to indicate this connection belongs to a shard, ignored for heads
        :return: The removed connection, None if it did not exist
        """
        if head:
            return await self._connections.remove_head(pod, address)
        else:
            if shard_id is None:
                shard_id = 0
            return await self._connections.remove_replica(pod, address, shard_id)

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

    def _send_messages(self, messages: List[Message], connection) -> asyncio.Task:
        # this wraps the awaitable object from grpc as a coroutine so it can be used as a task
        # the grpc call function is not a coroutine but some _AioCall
        async def task_wrapper(new_messages, stub):

            for i in range(3):
                try:
                    return await stub.Call(new_messages)
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

        return asyncio.create_task(task_wrapper(messages, connection))

    @staticmethod
    def activate_worker_sync(
        worker_host: str,
        worker_port: int,
        target_head: str,
        shard_id: Optional[int] = None,
    ) -> Message:
        """
        Register a given worker to a head by sending an activate message

        :param worker_host: the host address of the worker
        :param worker_port: the port of the worker
        :param target_head: address of the head to send the activate message to
        :param shard_id: id of the shard the worker belongs to
        :returns: the response message
        """
        activate_msg = ControlMessage(command='ACTIVATE')
        activate_msg.add_related_entity('worker', worker_host, worker_port, shard_id)
        return GrpcConnectionPool.send_message_sync(activate_msg, target_head)

    @staticmethod
    async def activate_worker(
        worker_host: str,
        worker_port: int,
        target_head: str,
        shard_id: Optional[int] = None,
    ) -> Message:
        """
        Register a given worker to a head by sending an activate message

        :param worker_host: the host address of the worker
        :param worker_port: the port of the worker
        :param target_head: address of the head to send the activate message to
        :param shard_id: id of the shard the worker belongs to
        :returns: the response message
        """
        activate_msg = ControlMessage(command='ACTIVATE')
        activate_msg.add_related_entity('worker', worker_host, worker_port, shard_id)
        return await GrpcConnectionPool.send_message_async(activate_msg, target_head)

    @staticmethod
    async def deactivate_worker(
        worker_host: str,
        worker_port: int,
        target_head: str,
        shard_id: Optional[int] = None,
    ) -> Message:
        """
        Remove a given worker to a head by sending a deactivate message

        :param worker_host: the host address of the worker
        :param worker_port: the port of the worker
        :param target_head: address of the head to send the deactivate message to
        :param shard_id: id of the shard the worker belongs to
        :returns: the response message
        """
        activate_msg = ControlMessage(command='DEACTIVATE')
        activate_msg.add_related_entity('worker', worker_host, worker_port, shard_id)
        return await GrpcConnectionPool.send_message_async(activate_msg, target_head)

    @staticmethod
    def send_message_sync(msg: Message, target: str, timeout=1.0) -> Message:
        """
        Sends a message synchronizly to the target via grpc

        :param msg: the message to send
        :param target: where to send the message to, like 127.0.0.1:8080
        :param timeout: timeout for the send
        :returns: the response message
        """

        for i in range(3):
            try:
                with grpc.insecure_channel(
                    target,
                    options=GrpcConnectionPool.get_default_grpc_options(),
                ) as channel:
                    stub = jina_pb2_grpc.JinaDataRequestRPCStub(channel)
                    response = stub.Call([msg], timeout=timeout)
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
    async def send_message_async(msg: Message, target: str, timeout=1.0) -> Message:
        """
        Sends a message synchronizly to the target via grpc

        :param msg: the message to send
        :param target: where to send the message to, like 127.0.0.1:8080
        :param timeout: timeout for the send
        :returns: the response message
        """

        async with grpc.aio.insecure_channel(
            target, options=GrpcConnectionPool.get_default_grpc_options()
        ) as channel:
            stub = jina_pb2_grpc.JinaDataRequestRPCStub(channel)
            return await stub.Call([msg], timeout=timeout)

    @staticmethod
    def send_messages_sync(
        messages: List[Message], target: str, timeout=1.0
    ) -> Message:
        """
        Sends messages synchronizly to the target via grpc

        :param messages: the list of messages to send
        :param target: where to send the message to, like 127.0.0.1:8080
        :param timeout: timeout for the send
        :returns: the response message
        """
        with grpc.insecure_channel(
            target, options=GrpcConnectionPool.get_default_grpc_options()
        ) as channel:
            stub = jina_pb2_grpc.JinaDataRequestRPCStub(channel)
            return stub.Call(messages, timeout=timeout)

    @staticmethod
    def create_async_channel_stub(
        address,
    ) -> Tuple[jina_pb2_grpc.JinaDataRequestRPCStub, grpc.aio.insecure_channel]:
        """
        Creates an async GRPC Channel. This channel has to be closed eventually!

        :param address: the adress to create the connection to, like 127.0.0.0.1:8080

        :returns: an async grpc channel
        """
        channel = grpc.aio.insecure_channel(
            address,
            options=GrpcConnectionPool.get_default_grpc_options(),
        )
        return jina_pb2_grpc.JinaDataRequestRPCStub(channel), channel


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
        jina_pod_name = item.metadata.labels['jina_pod_name']
        is_head = item.metadata.labels['pea_type'] == 'head'
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
                pod=jina_pod_name,
                head=is_head,
                address=f'{ip}:{port}',
                shard_id=shard_id,
            )
        elif ip and port and is_deleted and self._pod_is_up(item):
            await self.remove_connection(
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
        from jina.peapods.pods.k8slib.kubernetes_client import K8sClients

        k8s_clients = K8sClients()
        return K8sGrpcConnectionPool(
            namespace=k8s_namespace, client=k8s_clients.core_v1, logger=logger
        )
    else:
        return GrpcConnectionPool(logger=logger)
