import ast
import asyncio
import ipaddress
import socket
from abc import abstractmethod
from argparse import Namespace
from threading import Thread
from typing import Optional, TYPE_CHECKING

import grpc

from jina.logging.logger import JinaLogger
from jina.proto import jina_pb2_grpc
from jina.types.message import Message
from .. import __default_host__, __docker_host__
from ..helper import get_public_ip, get_internal_ip, get_or_reuse_loop

if TYPE_CHECKING:
    import kubernetes


class ConnectionList:
    """
    Maintains a list of connections and uses round roubin for selecting a connection

    :param port: port to use for the connections
    """

    def __init__(self, port: int):
        self.port = port
        self._connections = []
        self._address_to_connection_idx = {}
        self._rr_counter = 0

    def add_connection(self, address: str, connection):
        """
        Add connection with ip to the connection list
        :param address: Target address of this connection
        :param connection: The connection to add
        """
        if address not in self._address_to_connection_idx:
            self._address_to_connection_idx[address] = len(self._connections)
            self._connections.append(connection)

    def remove_connection(self, address: str):
        """
        Remove connection with ip from the connection list
        :param address: Remove connection for this address
        :returns: The removed connection or None if there was not any for the given ip
        """
        if address in self._address_to_connection_idx:
            self._rr_counter = (
                self._rr_counter % (len(self._connections) - 1)
                if (len(self._connections) - 1)
                else 0
            )
            return self._connections.pop(self._address_to_connection_idx.pop(address))

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

    def pop_connection(self):
        """
        Removes and returns a connection from the list. Strategy is round robin
        :returns: The connection removed from the pool
        """
        if self._connections:
            connection = self._connections.pop(self._rr_counter)
            self._rr_counter = (
                (self._rr_counter + 1) % len(self._connections)
                if len(self._connections)
                else 0
            )
            return connection
        else:
            return None

    def has_connection(self, address: str) -> bool:
        """
        Checks if a connection for ip exists in the list
        :param address: The address to check
        :returns: True if a connection for the ip exists in the list
        """
        return address in self._address_to_connection_idx


class ConnectionPool:
    """
    Manages a list of connections.

    :param logger: the logger to use
    :param on_demand_connection: Flag to indicate if connections should be created on demand
    """

    def __init__(self, logger: Optional[JinaLogger] = None, on_demand_connection=True):
        self._connections = {}
        self._on_demand_connection = on_demand_connection

        self._logger = logger or JinaLogger(self.__class__.__name__)

    def send_message(self, msg: Message, target_address: str):
        """Send msg to target_address via one of the pooled connections

        :param msg: message to send
        :param target_address: address to send to, should include the port like 1.1.1.1:53
        :return: result of the actual send method
        """
        if target_address in self._connections:
            pooled_connection = self._connections[target_address].get_next_connection()
            return self._send_message(msg, pooled_connection)
        elif self._on_demand_connection:
            # If the pool is disabled and an unknown connection is requested: create it
            connection_pool = self._create_connection_pool(target_address)
            return self._send_message(msg, connection_pool.get_next_connection())
        else:
            raise ValueError(f'Unknown address {target_address}')

    def _create_connection_pool(self, target_address):
        port = target_address[target_address.rfind(':') + 1 :]
        connection_pool = ConnectionList(port=port)
        connection_pool.add_connection(
            target_address, self._create_connection(target=target_address)
        )
        self._connections[target_address] = connection_pool
        return connection_pool

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

    @abstractmethod
    def _send_message(self, msg: Message, connection):
        ...

    @abstractmethod
    def _create_connection(self, target):
        ...


class GrpcConnectionPool(ConnectionPool):
    """
    GrpcConnectionPool which uses gRPC as the communication mechanism
    """

    def _send_message(self, msg: Message, connection):
        # this wraps the awaitable object from grpc as a coroutine so it can be used as a task
        # the grpc call function is not a coroutine but some _AioCall
        async def task_wrapper(new_message, stub):
            await stub.Call(new_message)

        return asyncio.create_task(task_wrapper(msg, connection))

    def _create_connection(self, target):
        self._logger.debug(f'create connection to {target}')
        channel = grpc.aio.insecure_channel(
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
        super().__init__(logger=logger, on_demand_connection=False)

        self._namespace = namespace
        self._deployment_clusteraddresses = {}
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

    def send_message(self, msg: Message, target_address: str):
        """
        Send msg to target_address via one of the pooled connections.

        :param msg: message to send
        :param target_address: address to send to, should include the port like 1.1.1.1:53
        :return: result of the actual send method
        """
        host, port = target_address.split(':')
        # host can be a domain instead of IP Address, resolve it to IP Address
        return super().send_message(msg, f'{socket.gethostbyname(host)}:{port}')

    @staticmethod
    def _pod_is_up(item):
        return item.status.pod_ip is not None and item.status.phase == 'Running'

    @staticmethod
    def _pod_is_ready(item):
        return item.status.container_statuses is not None and all(
            cs.ready for cs in item.status.container_statuses
        )

    def _process_item(self, item):
        deployment_name = item.metadata.labels["app"]
        is_deleted = item.metadata.deletion_timestamp is not None

        if not is_deleted and self._pod_is_up(item) and self._pod_is_ready(item):
            if deployment_name in self._deployment_clusteraddresses:
                self._add_pod_connection(deployment_name, item)
            else:
                cluster_ip, port = self._find_cluster_ip(deployment_name)
                if cluster_ip:
                    self._deployment_clusteraddresses[
                        deployment_name
                    ] = f'{cluster_ip}:{port}'
                    self._connections[f'{cluster_ip}:{port}'] = ConnectionList(port)
                    self._add_pod_connection(deployment_name, item)
                else:
                    self._logger.debug(
                        f'Observed state change in unknown deployment {deployment_name}'
                    )
        elif (
            is_deleted
            and self._pod_is_up(item)
            and deployment_name in self._deployment_clusteraddresses
        ):
            self._remove_pod_connection(deployment_name, item)

    def _remove_pod_connection(self, deployment_name, item):
        target = item.status.pod_ip
        connection_pool = self._connections[
            self._deployment_clusteraddresses[deployment_name]
        ]
        if connection_pool.has_connection(f'{target}:{connection_pool.port}'):
            self._logger.debug(
                f'Removing connection to {target}:{connection_pool.port} for deployment {deployment_name} at {self._deployment_clusteraddresses[deployment_name]}'
            )
            self._connections[
                self._deployment_clusteraddresses[deployment_name]
            ].remove_connection(f'{target}:{connection_pool.port}')

    def _add_pod_connection(self, deployment_name, item):
        target = item.status.pod_ip
        connection_pool = self._connections[
            self._deployment_clusteraddresses[deployment_name]
        ]
        if not connection_pool.has_connection(f'{target}:{connection_pool.port}'):
            self._logger.debug(
                f'Adding connection to {target}:{connection_pool.port} for deployment {deployment_name} at {self._deployment_clusteraddresses[deployment_name]}'
            )

            connection_pool.add_connection(
                f'{target}:{connection_pool.port}',
                self._create_connection(target=f'{target}:{connection_pool.port}'),
            )

    def _extract_app(self, service_item):
        if service_item.metadata.annotations:
            return ast.literal_eval(
                list(service_item.metadata.annotations.values())[0]
            )['spec']['selector']['app']
        elif service_item.metadata.labels:
            return service_item.metadata.labels['app']

        return None

    def _find_cluster_ip(self, deployment_name):
        service_resp = self._k8s_client.list_namespaced_service(self._namespace)
        for s in service_resp.items:
            app = self._extract_app(s)
            if app and deployment_name == app and s.spec.cluster_ip:
                # find the port-in for this deployment
                for p in s.spec.ports:
                    if p.name == 'port-in':
                        return s.spec.cluster_ip, p.port

        return None, None


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


def create_connection_pool(args: 'Namespace') -> ConnectionPool:
    """
    Creates the appropriate connection pool based on args
    :param args: Arguments for this pod
    :return: A connection pool object
    """
    if args.k8s_namespace and args.k8s_connection_pool:
        from jina.peapods.pods.k8slib.kubernetes_client import K8sClients

        k8s_clients = K8sClients()
        return K8sGrpcConnectionPool(
            namespace=args.k8s_namespace,
            client=k8s_clients.core_v1,
        )
    else:
        return GrpcConnectionPool()
