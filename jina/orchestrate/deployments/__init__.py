import copy
import json
import os
import re
import subprocess
from abc import abstractmethod
from argparse import Namespace
from collections import defaultdict
from contextlib import ExitStack
from itertools import cycle
from typing import Dict, List, Optional, Set, Union

from hubble.executor.helper import replace_secret_of_hub_uri
from hubble.executor.hubio import HubIO

from jina import __default_executor__, __default_host__, __docker_host__, helper
from jina.enums import DeploymentRoleType, PodRoleType, PollingType
from jina.helper import (
    CatchAllCleanupContextManager,
    parse_host_scheme,
)
from jina.orchestrate.pods.factory import PodFactory
from jina.parsers.helper import _update_gateway_args
from jina.serve.networking import host_is_local, in_docker

WRAPPED_SLICE_BASE = r'\[[-\d:]+\]'


class BaseDeployment(ExitStack):
    """A BaseDeployment is an immutable set of pods.
    Internally, the pods can run with the process/thread backend.
    They can be also run in their own containers on remote machines.
    """

    @abstractmethod
    def start(self) -> 'BaseDeployment':
        """Start to run all :class:`Pod` in this BaseDeployment.

        .. note::
            If one of the :class:`Pod` fails to start, make sure that all of them
            are properly closed.
        """
        ...

    @property
    def role(self) -> 'DeploymentRoleType':
        """Return the role of this :class:`BaseDeployment`.

        .. # noqa: DAR201
        """
        return self.args.deployment_role

    @property
    def name(self) -> str:
        """The name of this :class:`BaseDeployment`.


        .. # noqa: DAR201
        """
        return self.args.name

    @property
    def head_host(self) -> str:
        """Get the host of the HeadPod of this deployment
        .. # noqa: DAR201
        """
        return self.head_args.host if self.head_args else None

    @property
    def head_port(self):
        """Get the port of the HeadPod of this deployment
        .. # noqa: DAR201
        """
        return self.head_args.port if self.head_args else None

    @property
    def head_port_monitoring(self):
        """Get the port_monitoring of the HeadPod of this deployment
        .. # noqa: DAR201
        """
        return self.head_args.port_monitoring if self.head_args else None

    def __enter__(self) -> 'BaseDeployment':
        with CatchAllCleanupContextManager(self):
            return self.start()

    @staticmethod
    def _copy_to_head_args(args: Namespace) -> Namespace:
        """
        Set the outgoing args of the head router

        :param args: basic arguments
        :return: enriched head arguments
        """

        _head_args = copy.deepcopy(args)
        _head_args.polling = args.polling
        _head_args.port = args.port[0]
        _head_args.host = args.host[0]
        _head_args.uses = args.uses
        _head_args.pod_role = PodRoleType.HEAD
        _head_args.runtime_cls = 'HeadRuntime'
        _head_args.replicas = 1

        if args.name:
            _head_args.name = f'{args.name}/head'
        else:
            _head_args.name = f'head'

        return _head_args

    @property
    @abstractmethod
    def head_args(self) -> Namespace:
        """Get the arguments for the `head` of this BaseDeployment.

        .. # noqa: DAR201
        """
        ...

    @abstractmethod
    def join(self):
        """Wait until all deployment and pods exit."""
        ...

    @property
    @abstractmethod
    def _mermaid_str(self) -> List[str]:
        """String that will be used to represent the Deployment graphically when `Flow.plot()` is invoked


        .. # noqa: DAR201
        """
        ...

    @property
    def deployments(self) -> List[Dict]:
        """Get deployments of the deployment. The BaseDeployment just gives one deployment.

        :return: list of deployments
        """
        return [
            {
                'name': self.name,
                'head_host': self.head_host,
                'head_port': self.head_port,
            }
        ]


class Deployment(BaseDeployment):
    """A Deployment is an immutable set of pods, which run in replicas. They share the same input and output socket.
    Internally, the pods can run with the process/thread backend. They can be also run in their own containers
    :param args: arguments parsed from the CLI
    :param needs: deployments names of preceding deployments, the output of these deployments are going into the input of this deployment
    """

    class _ReplicaSet:
        def __init__(
            self,
            deployment_args: Namespace,
            args: List[Namespace],
            head_pod,
        ):
            self.deployment_args = copy.copy(deployment_args)
            self.args = args
            self.shard_id = args[0].shard_id
            self._pods = []
            self.head_pod = head_pod

        @property
        def is_ready(self):
            return all(p.is_ready.is_set() for p in self._pods)

        def clear_pods(self):
            self._pods.clear()

        @property
        def num_pods(self):
            return len(self._pods)

        def join(self):
            for pod in self._pods:
                pod.join()

        def wait_start_success(self):
            for pod in self._pods:
                pod.wait_start_success()

        def __enter__(self):
            for _args in self.args:
                if getattr(self.deployment_args, 'noblock_on_start', False):
                    _args.noblock_on_start = True
                self._pods.append(PodFactory.build_pod(_args).start())
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            closing_exception = None
            for pod in self._pods:
                try:
                    pod.close()
                except Exception as exc:
                    if closing_exception is None:
                        closing_exception = exc
            if exc_val is None and closing_exception is not None:
                raise closing_exception

    def __init__(
        self, args: Union['Namespace', Dict], needs: Optional[Set[str]] = None
    ):
        super().__init__()
        self.args = args
        self.args.polling = (
            args.polling if hasattr(args, 'polling') else PollingType.ANY
        )
        # polling only works for shards, if there are none, polling will be ignored
        if getattr(args, 'shards', 1) == 1:
            self.args.polling = PollingType.ANY
        self.needs = (
            needs or set()
        )  #: used in the :class:`jina.flow.Flow` to build the graph

        # parse addresses for distributed replicas
        (
            self.ext_repl_hosts,
            self.ext_repl_ports,
            self.ext_repl_schemes,
            self.ext_repl_tls,
        ) = ([], [], [], [])
        if self.args.pod_role != PodRoleType.GATEWAY:
            self._parse_external_replica_hosts_and_ports()
            self._parse_addresses_into_host_and_port()
        if len(self.ext_repl_ports) > 1:
            self.args.replicas = len(self.ext_repl_ports)

        self.uses_before_pod = None
        self.uses_after_pod = None
        self.head_pod = None
        self.shards = {}
        self._update_port_monitoring_args()
        self.update_pod_args()
        self._sandbox_deployed = False

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.join()

    def _parse_addresses_into_host_and_port(self):
        # splits addresses passed to `host` into separate `host` and `port`

        for i, _host in enumerate(self.args.host):
            _hostname, port, scheme, tls = parse_host_scheme(_host)
            if _hostname != _host:  # more than just hostname was passed to `host`
                self.args.host[i] = _hostname
                self.args.port[i] = port
                self.args.scheme = scheme
                self.args.tls = tls
        for i, repl_host in enumerate(self.ext_repl_hosts):
            _hostname, port, scheme, tls = parse_host_scheme(repl_host)
            if (
                _hostname != self.ext_repl_hosts[i]
            ):  # more than just hostname was passed to `host`
                self.ext_repl_hosts[i] = _hostname
                self.ext_repl_ports[i] = port
                self.ext_repl_schemes[i] = scheme
                self.ext_repl_tls[i] = tls

    def _parse_external_replica_hosts_and_ports(self):
        # splits user provided lists of hosts and ports into a host and port for every distributed replica
        ext_repl_ports: List = self.args.port.copy()
        ext_repl_hosts: List = self.args.host.copy()
        if len(ext_repl_hosts) < len(ext_repl_ports):
            if (
                len(ext_repl_hosts) == 1
            ):  # only one host given, assume replicas are on the same host
                ext_repl_hosts = ext_repl_hosts * len(ext_repl_ports)
                self.args.host = self.args.host * len(ext_repl_ports)
        elif len(ext_repl_hosts) > len(ext_repl_ports):
            if (
                len(ext_repl_ports) == 1
            ):  # only one port given, assume replicas are on the same port
                ext_repl_ports = ext_repl_ports * len(ext_repl_hosts)
                self.args.port = self.args.port * len(ext_repl_hosts)
        if len(ext_repl_hosts) != len(ext_repl_ports):
            raise ValueError(
                f'Number of hosts ({len(ext_repl_hosts)}) does not match the number of ports ({len(ext_repl_ports)})'
            )

        self.ext_repl_hosts, self.ext_repl_ports = ext_repl_hosts, ext_repl_ports
        # varying tls and schemes other than 'grpc' only implemented if the entire address is passed to `host`
        self.ext_repl_schemes = [
            getattr(self.args, 'scheme', None) for _ in self.ext_repl_ports
        ]
        self.ext_repl_tls = [
            getattr(self.args, 'tls', None) for _ in self.ext_repl_ports
        ]

    def _update_port_monitoring_args(self):
        # TODO: update this when port_monitoring is changed
        _all_port_monitoring = self.args.port_monitoring
        self.args.all_port_monitoring = (
            [_all_port_monitoring]
            if not type(_all_port_monitoring) == list
            else _all_port_monitoring
        )
        self.args.port_monitoring = int(
            self.args.all_port_monitoring[0]
        )  # this is for the head

    def update_pod_args(self):
        """Update args of all its pods based on Deployment args. Including head/tail"""
        if self.args.runtime_cls == 'GatewayRuntime':
            _update_gateway_args(self.args)
        if isinstance(self.args, Dict):
            # This is used when a Deployment is created in a remote context, where pods & their connections are already given.
            self.pod_args = self.args
        else:
            self.pod_args = self._parse_args(self.args)

    def update_sandbox_args(self):
        """Update args of all its pods based on the host and port returned by Hubble"""
        if self.is_sandbox:
            host, port = HubIO.deploy_public_sandbox(self.args)
            self._sandbox_deployed = True
            self.first_pod_args.host = host
            self.first_pod_args.port = port
            if self.head_args:
                self.pod_args['head'].host = host
                self.pod_args['head'].port = port

    def update_worker_pod_args(self):
        """Update args of all its worker pods based on Deployment args. Does not touch head and tail"""
        self.pod_args['pods'] = self._set_pod_args()

    @property
    def is_sandbox(self) -> bool:
        """
        Check if this deployment is a sandbox.

        :return: True if this deployment is provided as a sandbox, False otherwise
        """
        from hubble.executor.helper import is_valid_sandbox_uri

        uses = getattr(self.args, 'uses') or ''
        return is_valid_sandbox_uri(uses)

    @property
    def _is_docker(self) -> bool:
        """
        Check if this deployment is to be run in docker.

        :return: True if this deployment is to be run in docker
        """
        from hubble.executor.helper import is_valid_docker_uri

        uses = getattr(self.args, 'uses', '')
        return is_valid_docker_uri(uses)

    @property
    def _is_executor_from_yaml(self) -> bool:
        """
        Check if this deployment is to be run from YAML configuration.

        :return: True if this deployment is to be run from YAML configuration
        """
        uses = getattr(self.args, 'uses', '')
        return uses.endswith('yml') or uses.endswith('yaml')

    @property
    def tls_enabled(self):
        """
        Checks whether secure connection via tls is enabled for this Deployment.

        :return: True if tls is enabled, False otherwise
        """
        has_cert = getattr(self.args, 'ssl_certfile', None) is not None
        has_key = getattr(self.args, 'ssl_keyfile', None) is not None
        tls = getattr(self.args, 'tls', False)
        return tls or self.is_sandbox or (has_cert and has_key)

    @property
    def external(self) -> bool:
        """
        Check if this deployment is external.

        :return: True if this deployment is provided as an external deployment, False otherwise
        """
        return getattr(self.args, 'external', False) or self.is_sandbox

    @property
    def grpc_metadata(self):
        """
        Get the gRPC metadata for this deployment.
        :return: The gRPC metadata for this deployment. If the deployment is a gateway, return None.
        """
        return getattr(self.args, 'grpc_metadata', None)

    @property
    def protocol(self):
        """
        :return: the protocol of this deployment
        """
        protocol = getattr(self.args, 'protocol', ['grpc'])
        if not isinstance(protocol, list):
            protocol = [protocol]
        protocol = [str(_p) + ('s' if self.tls_enabled else '') for _p in protocol]
        if len(protocol) == 1:
            return protocol[0]
        else:
            return protocol

    @property
    def first_pod_args(self) -> Namespace:
        """Return the first worker pod's args


        .. # noqa: DAR201
        """
        # note this will be never out of boundary
        return self.pod_args['pods'][0][0]

    @property
    def host(self) -> str:
        """Get the host name of this deployment


        .. # noqa: DAR201
        """
        return self.first_pod_args.host

    @property
    def port(self):
        """
        :return: the port of this deployment
        """
        return self.first_pod_args.port

    @property
    def ports(self) -> List[int]:
        """Returns a list of ports exposed by this Deployment.
        Exposed means these are the ports a Client/Gateway is supposed to communicate with.
        For sharded deployments this will be the head_port.
        For non-sharded deployments it will be all replica ports
        .. # noqa: DAR201
        """
        if self.head_port:
            return [self.head_port]
        else:
            ports = []
            for replica in self.pod_args['pods'][0]:
                if isinstance(replica.port, list):
                    ports.extend(replica.port)
                else:
                    ports.append(replica.port)
            return ports

    @property
    def hosts(self) -> List[str]:
        """Returns a list of host addresses exposed by this Deployment.
        Exposed means these are the host a Client/Gateway is supposed to communicate with.
        For sharded deployments this will be the head host.
        For non-sharded deployments it will be all replica hosts
        .. # noqa: DAR201
        """
        if self.head_host:
            return [self.head_host]
        else:
            return [replica.host for replica in self.pod_args['pods'][0]]

    @property
    def dockerized_uses(self) -> bool:
        """Checks if this Deployment uses a dockerized Executor

        .. # noqa: DAR201
        """
        return self.args.uses.startswith('docker://') or self.args.uses.startswith(
            'jinahub+docker://'
        )

    def _parse_args(
        self, args: Namespace
    ) -> Dict[str, Optional[Union[List[Namespace], Namespace]]]:
        return self._parse_base_deployment_args(args)

    @property
    def head_args(self) -> Namespace:
        """Get the arguments for the `head` of this Deployment.


        .. # noqa: DAR201
        """
        return self.pod_args['head']

    @head_args.setter
    def head_args(self, args):
        """Set the arguments for the `head` of this Deployment.


        .. # noqa: DAR101
        """
        self.pod_args['head'] = args

    @property
    def uses_before_args(self) -> Namespace:
        """Get the arguments for the `uses_before` of this Deployment.


        .. # noqa: DAR201
        """
        return self.pod_args['uses_before']

    @uses_before_args.setter
    def uses_before_args(self, args):
        """Set the arguments for the `uses_before` of this Deployment.


        .. # noqa: DAR101
        """
        self.pod_args['uses_before'] = args

    @property
    def uses_after_args(self) -> Namespace:
        """Get the arguments for the `uses_after` of this Deployment.


        .. # noqa: DAR201
        """
        return self.pod_args['uses_after']

    @uses_after_args.setter
    def uses_after_args(self, args):
        """Set the arguments for the `uses_after` of this Deployment.


        .. # noqa: DAR101
        """
        self.pod_args['uses_after'] = args

    @property
    def all_args(self) -> List[Namespace]:
        """Get all arguments of all Pods in this BaseDeployment.

        .. # noqa: DAR201
        """
        all_args = (
            ([self.pod_args['uses_before']] if self.pod_args['uses_before'] else [])
            + ([self.pod_args['uses_after']] if self.pod_args['uses_after'] else [])
            + ([self.pod_args['head']] if self.pod_args['head'] else [])
        )
        for shard_id in self.pod_args['pods']:
            all_args += self.pod_args['pods'][shard_id]
        return all_args

    @property
    def num_pods(self) -> int:
        """Get the number of running :class:`Pod`

        .. # noqa: DAR201
        """
        num_pods = 0
        if self.head_pod is not None:
            num_pods += 1
        if self.uses_before_pod is not None:
            num_pods += 1
        if self.uses_after_pod is not None:
            num_pods += 1
        if self.shards:  # external deployments
            for shard_id in self.shards:
                num_pods += self.shards[shard_id].num_pods
        return num_pods

    def __eq__(self, other: 'BaseDeployment'):
        return self.num_pods == other.num_pods and self.name == other.name

    @staticmethod
    def get_worker_host(pod_args, pod_is_container, head_is_container):
        """
        Check if the current pod and head are both containerized on the same host
        If so __docker_host__ needs to be advertised as the worker's address to the head

        :param pod_args: arguments of the worker pod
        :param pod_is_container: boolean specifying if pod is to be run in container
        :param head_is_container: boolean specifying if head pod is to be run in container
        :return: host to pass in connection list of the head
        """
        # Check if the current pod and head are both containerized on the same host
        # If so __docker_host__ needs to be advertised as the worker's address to the head
        worker_host = (
            __docker_host__
            if (pod_is_container and (head_is_container or in_docker()))
            and host_is_local(pod_args.host)
            else pod_args.host
        )
        return worker_host

    def start(self) -> 'Deployment':
        """
        Start to run all :class:`Pod` in this BaseDeployment.

        :return: started deployment

        .. note::
            If one of the :class:`Pod` fails to start, make sure that all of them
            are properly closed.
        """
        if self.is_sandbox and not self._sandbox_deployed:
            self.update_sandbox_args()

        if self.pod_args['uses_before'] is not None:
            _args = self.pod_args['uses_before']
            if getattr(self.args, 'noblock_on_start', False):
                _args.noblock_on_start = True
            self.uses_before_pod = PodFactory.build_pod(_args)
            self.enter_context(self.uses_before_pod)
        if self.pod_args['uses_after'] is not None:
            _args = self.pod_args['uses_after']
            if getattr(self.args, 'noblock_on_start', False):
                _args.noblock_on_start = True
            self.uses_after_pod = PodFactory.build_pod(_args)
            self.enter_context(self.uses_after_pod)
        if self.pod_args['head'] is not None:
            _args = self.pod_args['head']
            if getattr(self.args, 'noblock_on_start', False):
                _args.noblock_on_start = True
            self.head_pod = PodFactory.build_pod(_args)
            self.enter_context(self.head_pod)
        for shard_id in self.pod_args['pods']:
            self.shards[shard_id] = self._ReplicaSet(
                self.args,
                self.pod_args['pods'][shard_id],
                self.head_pod,
            )
            self.enter_context(self.shards[shard_id])

        return self

    def wait_start_success(self) -> None:
        """Block until all pods starts successfully.

        If not successful, it will raise an error hoping the outer function to catch it
        """
        if not self.args.noblock_on_start:
            raise ValueError(
                f'{self.wait_start_success!r} should only be called when `noblock_on_start` is set to True'
            )
        try:
            if self.uses_before_pod is not None:
                self.uses_before_pod.wait_start_success()
            if self.uses_after_pod is not None:
                self.uses_after_pod.wait_start_success()
            if self.head_pod is not None:
                self.head_pod.wait_start_success()
            for shard_id in self.shards:
                self.shards[shard_id].wait_start_success()
        except:
            self.close()
            raise

    def join(self):
        """Wait until all pods exit"""
        try:
            if self.uses_before_pod is not None:
                self.uses_before_pod.join()
            if self.uses_after_pod is not None:
                self.uses_after_pod.join()
            if self.head_pod is not None:
                self.head_pod.join()
            if self.shards:
                for shard_id in self.shards:
                    self.shards[shard_id].join()
        except KeyboardInterrupt:
            pass
        finally:
            self.head_pod = None
            if self.shards:
                for shard_id in self.shards:
                    self.shards[shard_id].clear_pods()

    @property
    def is_ready(self) -> bool:
        """Checks if Deployment is ready

        .. note::
            A Deployment is ready when all the Pods it contains are ready


        .. # noqa: DAR201
        """
        is_ready = True
        if self.head_pod is not None:
            is_ready = self.head_pod.is_ready.is_set()
        if is_ready:
            for shard_id in self.shards:
                is_ready = self.shards[shard_id].is_ready
        if is_ready and self.uses_before_pod is not None:
            is_ready = self.uses_before_pod.is_ready.is_set()
        if is_ready and self.uses_after_pod is not None:
            is_ready = self.uses_after_pod.is_ready.is_set()
        return is_ready

    @staticmethod
    def _parse_devices(value: str, num_devices: int):
        """Parses a list of devices from string, like `start:stop:step` or 'num1,num2,num3` or combination of both.

        :param value: a string like
        :param num_devices: total number of devices
        :return: slice
        """

        use_uuids = False
        if re.match(WRAPPED_SLICE_BASE, value):
            value = value[1:-1]

        if value:
            parts = value.split(',')
            if len(parts) == 1:
                parts = value.split(':')

                if len(parts) == 1:
                    try:
                        int(parts[0])
                    except:
                        use_uuids = True
                    if use_uuids:
                        return parts
                    parts = [parts[0], str(int(parts[0]) + 1)]
            else:
                # try to detect if parts are not numbers
                try:
                    int(parts[0])
                except:
                    use_uuids = True

                if not use_uuids:
                    return [int(p) for p in parts]
                else:
                    return parts
        else:
            parts = []

        all_devices = range(num_devices)
        return all_devices[slice(*[int(p) if p else None for p in parts])]

    @staticmethod
    def _roundrobin_cuda_device(device_str: str, replicas: int):
        """Parse cuda device string with RR prefix

        :param device_str: `RRm:n`, where `RR` is the prefix, m:n is python slice format
        :param replicas: the number of replicas
        :return: a map from replica id to device id
        """
        if (
            device_str
            and isinstance(device_str, str)
            and device_str.startswith('RR')
            and replicas >= 1
        ):
            try:
                num_devices = str(subprocess.check_output(['nvidia-smi', '-L'])).count(
                    'UUID'
                )
            except:
                num_devices = int(os.environ.get('CUDA_TOTAL_DEVICES', 0))
                if num_devices == 0:
                    return

            selected_devices = []
            if device_str[2:]:

                for device in Deployment._parse_devices(device_str[2:], num_devices):
                    selected_devices.append(device)
            else:
                selected_devices = range(num_devices)
            _c = cycle(selected_devices)
            return {j: next(_c) for j in range(replicas)}

    def _set_pod_args(self) -> Dict[int, List[Namespace]]:
        result = {}
        shards = getattr(self.args, 'shards', 1)
        replicas = getattr(self.args, 'replicas', 1)
        sharding_enabled = shards and shards > 1

        cuda_device_map = None
        if self.args.env:
            cuda_device_map = Deployment._roundrobin_cuda_device(
                self.args.env.get('CUDA_VISIBLE_DEVICES'), replicas
            )

        for shard_id in range(shards):
            replica_args = []
            for replica_id in range(replicas):
                _args = copy.deepcopy(self.args)
                _args.shard_id = shard_id
                # for gateway pods, the pod role shouldn't be changed
                if _args.pod_role != PodRoleType.GATEWAY:
                    _args.pod_role = PodRoleType.WORKER
                    if len(self.args.host) == 1:
                        _args.host = self.args.host[0]
                    elif len(self.args.host) == replicas:
                        _args.host = self.args.host[replica_id]
                    else:
                        raise ValueError(
                            f'Number of hosts ({len(self.args.host)}) does not match the number of replicas ({replicas})'
                        )
                else:
                    _args.host = self.args.host

                if cuda_device_map:
                    _args.env['CUDA_VISIBLE_DEVICES'] = str(cuda_device_map[replica_id])
                
                if _args.name:
                    _args.name += (
                        f'/shard-{shard_id}/rep-{replica_id}'
                        if sharding_enabled
                        else f'/rep-{replica_id}'
                    )
                else:
                    _args.name = f'{replica_id}'

                # the gateway needs to respect the assigned port
                if self.args.deployment_role == DeploymentRoleType.GATEWAY:
                    _args.port = self.args.port
                
                elif not self.external:
                    if shards == 1 and replicas == 1:
                        _args.port = self.args.port[0]
                        _args.port_monitoring = self.args.port_monitoring

                    elif shards == 1:
                        _args.port_monitoring = (
                            helper.random_port()
                            if replica_id >= len(self.args.all_port_monitoring)
                            else self.args.all_port_monitoring[replica_id]
                        )
                        # if there are no shards/replicas, we dont need to distribute ports randomly
                        # we should rather use the pre assigned one
                        _args.port = helper.random_port()
                    elif shards > 1:
                        port_monitoring_index = (
                            replica_id + replicas * shard_id + 1
                        )  # the first index is for the head
                        _args.port_monitoring = (
                            helper.random_port()
                            if port_monitoring_index >= len(self.args.all_port_monitoring)
                            else self.args.all_port_monitoring[
                                port_monitoring_index
                            ]  # we skip the head port here
                        )
                        _args.port = helper.random_port()
                    else:
                        _args.port = helper.random_port()
                        _args.port_monitoring = helper.random_port()
                
                else:
                    # if shards > 1:
                    #     raise ValueError(
                    #         f'external deployment with multiple shards is not supported'
                    #     )
                    _args.port = self.ext_repl_ports[replica_id]
                    _args.host = self.ext_repl_hosts[replica_id]
                    _args.scheme = self.ext_repl_schemes[replica_id]
                    _args.tls = self.ext_repl_tls[replica_id]

                # pod workspace if not set then derive from workspace
                if not _args.workspace:
                    _args.workspace = self.args.workspace
                replica_args.append(_args)
                print('_set_pod_args!!!', _args.host, _args.port)
            result[shard_id] = replica_args
        return result

    @staticmethod
    def _set_uses_before_after_args(args: Namespace, entity_type: str) -> Namespace:

        _args = copy.deepcopy(args)
        _args.pod_role = PodRoleType.WORKER
        _args.host = _args.host[0] or __default_host__
        print('uses_before_after _args.host = args.host[0]', _args.host)
        _args.port = helper.random_port()

        if _args.name:
            _args.name += f'/{entity_type}-0'
        else:
            _args.name = f'{entity_type}-0'

        if 'uses_before' == entity_type:
            _args.uses_requests = None
            _args.uses = args.uses_before or __default_executor__
        elif 'uses_after' == entity_type:
            _args.uses_requests = None
            _args.uses = args.uses_after or __default_executor__
        else:
            raise ValueError(
                f'uses_before/uses_after pod does not support type {entity_type}'
            )

        # pod workspace if not set then derive from workspace
        if not _args.workspace:
            _args.workspace = args.workspace
        return _args

    def _parse_base_deployment_args(self, args):
        parsed_args = {
            'head': None,
            'uses_before': None,
            'uses_after': None,
            'pods': {},
        }

        # a gateway has no heads and uses
        # also there a no heads created, if there are no shards
        if self.role != DeploymentRoleType.GATEWAY and getattr(args, 'shards', 1) > 1:
            if (
                getattr(args, 'uses_before', None)
                and args.uses_before != __default_executor__
            ):
                uses_before_args = self._set_uses_before_after_args(
                    args, entity_type='uses_before'
                )
                parsed_args['uses_before'] = uses_before_args
                args.uses_before_address = (
                    f'{uses_before_args.host}:{uses_before_args.port}'
                )
            if (
                getattr(args, 'uses_after', None)
                and args.uses_after != __default_executor__
            ):
                uses_after_args = self._set_uses_before_after_args(
                    args, entity_type='uses_after'
                )
                parsed_args['uses_after'] = uses_after_args
                args.uses_after_address = (
                    f'{uses_after_args.host}:{uses_after_args.port}'
                )

            parsed_args['head'] = BaseDeployment._copy_to_head_args(args)

        parsed_args['pods'] = self._set_pod_args()

        if parsed_args['head'] is not None:
            connection_list = defaultdict(list)

            for shard_id in parsed_args['pods']:
                for pod_idx, pod_args in enumerate(parsed_args['pods'][shard_id]):
                    worker_host = self.get_worker_host(pod_args, self._is_docker, False)
                    connection_list[shard_id].append(f'{worker_host}:{pod_args.port}')
            parsed_args['head'].connection_list = json.dumps(connection_list)

        return parsed_args

    @property
    def _mermaid_str(self) -> List[str]:
        """String that will be used to represent the Deployment graphically when `Flow.plot()` is invoked.
        It does not include used_before/uses_after


        .. # noqa: DAR201
        """
        mermaid_graph = []
        secret = '&ltsecret&gt'
        if self.role != DeploymentRoleType.GATEWAY and not self.external:
            mermaid_graph = [f'subgraph {self.name};', f'\ndirection LR;\n']

            uses_before_name = (
                self.uses_before_args.name
                if self.uses_before_args is not None
                else None
            )
            uses_before_uses = (
                replace_secret_of_hub_uri(self.uses_before_args.uses, secret)
                if self.uses_before_args is not None
                else None
            )
            uses_after_name = (
                self.uses_after_args.name if self.uses_after_args is not None else None
            )
            uses_after_uses = (
                replace_secret_of_hub_uri(self.uses_after_args.uses, secret)
                if self.uses_after_args is not None
                else None
            )
            shard_names = []
            if len(self.pod_args['pods']) > 1:
                # multiple shards
                for shard_id, pod_args in self.pod_args['pods'].items():
                    shard_name = f'{self.name}/shard-{shard_id}'
                    shard_names.append(shard_name)
                    shard_mermaid_graph = [
                        f'subgraph {shard_name};',
                        f'\ndirection TB;\n',
                    ]
                    names = [
                        args.name for args in pod_args
                    ]  # all the names of each of the replicas
                    uses = [
                        args.uses for args in pod_args
                    ]  # all the uses should be the same but let's keep it this
                    # way
                    for rep_i, (name, use) in enumerate(zip(names, uses)):
                        escaped_uses = f'"{replace_secret_of_hub_uri(use, secret)}"'
                        shard_mermaid_graph.append(f'{name}[{escaped_uses}]:::pod;')
                    shard_mermaid_graph.append('end;')
                    shard_mermaid_graph = [
                        node.replace(';', '\n') for node in shard_mermaid_graph
                    ]
                    mermaid_graph.extend(shard_mermaid_graph)
                    mermaid_graph.append('\n')
                if uses_before_name is not None:
                    for shard_name in shard_names:
                        escaped_uses_before_uses = (
                            f'"{replace_secret_of_hub_uri(uses_before_uses, secret)}"'
                        )
                        mermaid_graph.append(
                            f'{self.args.name}-head[{escaped_uses_before_uses}]:::HEADTAIL --> {shard_name};'
                        )
                if uses_after_name is not None:
                    for shard_name in shard_names:
                        escaped_uses_after_uses = f'"{uses_after_uses}"'
                        mermaid_graph.append(
                            f'{shard_name} --> {self.args.name}-tail[{escaped_uses_after_uses}]:::HEADTAIL;'
                        )
            else:
                # single shard case, no uses_before or uses_after_considered
                pod_args = list(self.pod_args['pods'].values())[0][0]
                uses = f'"{replace_secret_of_hub_uri(pod_args.uses, secret)}"'

                # just put the replicas in parallel
                if pod_args.replicas > 1:
                    for rep_i in range(pod_args.replicas):
                        mermaid_graph.append(
                            f'{pod_args.name}/rep-{rep_i}["{uses}"]:::pod;'
                        )
                else:
                    mermaid_graph.append(f'{pod_args.name}["{uses}"]:::pod;')

            mermaid_graph.append('end;')
        return mermaid_graph
