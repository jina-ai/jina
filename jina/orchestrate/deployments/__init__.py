import copy
import os
from abc import abstractmethod
from argparse import Namespace
from contextlib import ExitStack
from typing import Dict, List, Optional, Set, Union

from jina import __default_executor__, __default_host__, __docker_host__, helper
from jina.enums import DeploymentRoleType, PodRoleType, PollingType
from jina.helper import CatchAllCleanupContextManager
from jina.hubble.hubio import HubIO
from jina.jaml.helper import complete_path
from jina.orchestrate.pods.container import ContainerPod
from jina.orchestrate.pods.factory import PodFactory
from jina.serve.networking import GrpcConnectionPool, host_is_local, in_docker


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

    @staticmethod
    def _set_upload_files(args):
        # sets args.upload_files at the deployment level so that pods inherit from it.
        # all pods work under one remote workspace, hence important to have upload_files set for all

        def valid_path(path):
            try:
                complete_path(path)
                return True
            except FileNotFoundError:
                return False

        _upload_files = set()
        for param in ['uses', 'uses_before', 'uses_after']:
            param_value = getattr(args, param, None)
            if param_value and valid_path(param_value):
                _upload_files.add(param_value)

        if getattr(args, 'py_modules', None):
            _upload_files.update(
                {py_module for py_module in args.py_modules if valid_path(py_module)}
            )
        if getattr(args, 'upload_files', None):
            _upload_files.update(
                {
                    upload_file
                    for upload_file in args.upload_files
                    if valid_path(upload_file)
                }
            )
        return list(_upload_files)

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
        if not hasattr(args, 'port') or not args.port:
            _head_args.port = helper.random_port()
        else:
            _head_args.port = args.port
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
        args.upload_files = BaseDeployment._set_upload_files(args)
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

        self.uses_before_pod = None
        self.uses_after_pod = None
        self.head_pod = None
        self.shards = {}
        self.update_pod_args()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.join()

    def update_pod_args(self):
        """Update args of all its pods based on Deployment args. Including head/tail"""
        if isinstance(self.args, Dict):
            # This is used when a Deployment is created in a remote context, where pods & their connections are already given.
            self.pod_args = self.args
        else:
            self.pod_args = self._parse_args(self.args)

        if self.is_sandbox:
            host, port = HubIO.deploy_public_sandbox(self.args)
            self.first_pod_args.host = host
            self.first_pod_args.port = port
            if self.head_args:
                self.pod_args['head'].host = host
                self.pod_args['head'].port = port

    def update_worker_pod_args(self):
        """Update args of all its worker pods based on Deployment args. Does not touch head and tail"""
        self.pod_args['pods'] = self._set_pod_args(self.args)

    @property
    def is_sandbox(self) -> bool:
        """
        Check if this deployment is a sandbox.

        :return: True if this deployment is provided as a sandbox, False otherwise
        """
        uses = getattr(self.args, 'uses', '')
        is_sandbox = uses.startswith('jinahub+sandbox://')
        return is_sandbox

    @property
    def tls_enabled(self):
        """
        Checks whether secure connection via tls is enabled for this Deployment.

        :return: True if tls is enabled, False otherwise
        """
        has_cert = getattr(self.args, 'ssl_certfile', None) is not None
        has_key = getattr(self.args, 'ssl_keyfile', None) is not None
        return self.is_sandbox or (has_cert and has_key)

    @property
    def external(self) -> bool:
        """
        Check if this deployment is external.

        :return: True if this deployment is provided as an external deployment, False otherwise
        """
        return getattr(self.args, 'external', False) or self.is_sandbox

    @property
    def protocol(self):
        """
        :return: the protocol of this deployment
        """
        protocol = getattr(self.args, 'protocol', 'grpc')
        return str(protocol) + ('s' if self.tls_enabled else '')

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
        For non sharded deployments it will be all replica ports
        .. # noqa: DAR201
        """
        if self.head_port:
            return [self.head_port]
        else:
            ports = []
            for replica in self.pod_args['pods'][0]:
                ports.append(replica.port)
            return ports

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

    def activate(self):
        """
        Activate all worker pods in this deployment by registering them with the head
        """
        if self.head_pod is not None:
            for shard_id in self.pod_args['pods']:
                for pod_idx, pod_args in enumerate(self.pod_args['pods'][shard_id]):
                    worker_host = self.get_worker_host(
                        pod_args, self.shards[shard_id]._pods[pod_idx], self.head_pod
                    )
                    GrpcConnectionPool.activate_worker_sync(
                        worker_host,
                        int(pod_args.port),
                        self.head_pod.runtime_ctrl_address,
                        shard_id,
                    )

    @staticmethod
    def get_worker_host(pod_args, pod, head_pod):
        """
        Check if the current pod and head are both containerized on the same host
        If so __docker_host__ needs to be advertised as the worker's address to the head

        :param pod_args: arguments of the worker pod
        :param pod: the worker pod
        :param head_pod: head pod communicating with the worker pod
        :return: host to use in activate messages
        """
        # Check if the current pod and head are both containerized on the same host
        # If so __docker_host__ needs to be advertised as the worker's address to the head
        worker_host = (
            __docker_host__
            if Deployment._is_container_to_container(pod, head_pod)
            and host_is_local(pod_args.host)
            else pod_args.host
        )
        return worker_host

    @staticmethod
    def _is_container_to_container(pod, head_pod):
        # Check if both shard_id/pod_idx and the head are containerized
        # if the head is not containerized, it still could mean that the deployment itself is containerized
        return type(pod) == ContainerPod and (
            type(head_pod) == ContainerPod or in_docker()
        )

    def start(self) -> 'Deployment':
        """
        Start to run all :class:`Pod` in this BaseDeployment.

        :return: started deployment

        .. note::
            If one of the :class:`Pod` fails to start, make sure that all of them
            are properly closed.
        """
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

        if not getattr(self.args, 'noblock_on_start', False):
            self.activate()
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
            self.activate()
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
    def _set_pod_args(args: Namespace) -> Dict[int, List[Namespace]]:
        result = {}
        sharding_enabled = args.shards and args.shards > 1
        for shard_id in range(args.shards):
            replica_args = []
            for replica_id in range(args.replicas):
                _args = copy.deepcopy(args)
                _args.shard_id = shard_id
                _args.pod_role = PodRoleType.WORKER

                _args.host = args.host
                if _args.name:
                    _args.name += (
                        f'/shard-{shard_id}/rep-{replica_id}'
                        if sharding_enabled
                        else f'/rep-{replica_id}'
                    )
                else:
                    _args.name = f'{replica_id}'

                # the gateway needs to respect the assigned port
                if args.deployment_role == DeploymentRoleType.GATEWAY or args.external:
                    _args.port = args.port
                elif args.shards == 1 and args.replicas == 1:
                    # if there are no shards/replicas, we dont need to distribute ports randomly
                    # we should rather use the pre assigned one
                    args.port = args.port
                else:
                    _args.port = helper.random_port()

                # pod workspace if not set then derive from workspace
                if not _args.workspace:
                    _args.workspace = args.workspace
                replica_args.append(_args)
            result[shard_id] = replica_args
        return result

    @staticmethod
    def _set_uses_before_after_args(args: Namespace, entity_type: str) -> Namespace:

        _args = copy.deepcopy(args)
        _args.pod_role = PodRoleType.WORKER
        _args.host = __default_host__
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
        parsed_args['pods'] = self._set_pod_args(args)

        return parsed_args

    @property
    def _mermaid_str(self) -> List[str]:
        """String that will be used to represent the Deployment graphically when `Flow.plot()` is invoked.
        It does not include used_before/uses_after


        .. # noqa: DAR201
        """
        mermaid_graph = []
        if self.role != DeploymentRoleType.GATEWAY and not self.external:
            mermaid_graph = [f'subgraph {self.name};', f'\ndirection LR;\n']

            uses_before_name = (
                self.uses_before_args.name
                if self.uses_before_args is not None
                else None
            )
            uses_before_uses = (
                self.uses_before_args.uses
                if self.uses_before_args is not None
                else None
            )
            uses_after_name = (
                self.uses_after_args.name if self.uses_after_args is not None else None
            )
            uses_after_uses = (
                self.uses_after_args.uses if self.uses_after_args is not None else None
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
                        shard_mermaid_graph.append(f'{name}[{use}]:::pod;')
                    shard_mermaid_graph.append('end;')
                    shard_mermaid_graph = [
                        node.replace(';', '\n') for node in shard_mermaid_graph
                    ]
                    mermaid_graph.extend(shard_mermaid_graph)
                    mermaid_graph.append('\n')
                if uses_before_name is not None:
                    for shard_name in shard_names:
                        mermaid_graph.append(
                            f'{self.args.name}-head[{uses_before_uses}]:::HEADTAIL --> {shard_name};'
                        )
                if uses_after_name is not None:
                    for shard_name in shard_names:
                        mermaid_graph.append(
                            f'{shard_name} --> {self.args.name}-tail[{uses_after_uses}]:::HEADTAIL;'
                        )
            else:
                # single shard case, no uses_before or uses_after_considered
                name = list(self.pod_args['pods'].values())[0][0].name
                uses = list(self.pod_args['pods'].values())[0][0].uses
                num_replicas = list(self.pod_args['pods'].values())[0][0].replicas

                # just put the replicas in parallel
                if num_replicas > 1:
                    for rep_i in range(num_replicas):
                        mermaid_graph.append(f'{name}/rep-{rep_i}[{uses}]:::pod;')
                else:
                    mermaid_graph.append(f'{name}[{uses}]:::pod;')
            mermaid_graph.append('end;')
        return mermaid_graph
