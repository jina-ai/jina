import copy
import os
from abc import abstractmethod
from argparse import Namespace
from contextlib import ExitStack
from itertools import cycle
from typing import Dict, Union, Set, List, Optional

from jina.peapods import Pea
from jina.peapods.networking import GrpcConnectionPool, host_is_local
from jina.peapods.peas.container import ContainerPea
from jina.peapods.peas.factory import PeaFactory
from jina.peapods.peas.jinad import JinaDPea
from jina import __default_executor__, __default_host__, __docker_host__
from jina import helper
from jina.enums import PodRoleType, PeaRoleType, PollingType
from jina.excepts import RuntimeFailToStart, RuntimeRunForeverEarlyError, ScalingFails
from jina.helper import random_identity, CatchAllCleanupContextManager
from jina.jaml.helper import complete_path


class BasePod(ExitStack):
    """A BasePod is an immutable set of peas.
    Internally, the peas can run with the process/thread backend.
    They can be also run in their own containers on remote machines.
    """

    @abstractmethod
    def start(self) -> 'BasePod':
        """Start to run all :class:`Pea` in this BasePod.

        .. note::
            If one of the :class:`Pea` fails to start, make sure that all of them
            are properly closed.
        """
        ...

    @abstractmethod
    async def rolling_update(self, *args, **kwargs):
        """
        Roll update the Executors managed by the Pod

            .. # noqa: DAR201
            .. # noqa: DAR101
        """
        ...

    @abstractmethod
    async def scale(self, *args, **kwargs):
        """
        Scale the amount of replicas of a given Executor.

            .. # noqa: DAR201
            .. # noqa: DAR101
        """
        ...

    @staticmethod
    def _set_upload_files(args):
        # sets args.upload_files at the pod level so that peas inherit from it.
        # all peas work under one remote workspace, hence important to have upload_files set for all

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
    def role(self) -> 'PodRoleType':
        """Return the role of this :class:`BasePod`.

        .. # noqa: DAR201
        """
        return self.args.pod_role

    @property
    def name(self) -> str:
        """The name of this :class:`BasePod`.


        .. # noqa: DAR201
        """
        return self.args.name

    @property
    def head_host(self) -> str:
        """Get the host of the HeadPea of this pod
        .. # noqa: DAR201
        """
        return self.head_args.host

    @property
    def head_port_in(self):
        """Get the port_in of the HeadPea of this pod
        .. # noqa: DAR201
        """
        return self.head_args.port_in

    def __enter__(self) -> 'BasePod':
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
        if not hasattr(args, 'port_in') or not args.port_in:
            _head_args.port_in = helper.random_port()
        else:
            _head_args.port_in = args.port_in
        _head_args.uses = args.uses
        _head_args.pea_role = PeaRoleType.HEAD
        _head_args.runtime_cls = 'HeadRuntime'
        _head_args.replicas = 1

        # for now the head is not being scaled, so its always the first head
        if args.name:
            _head_args.name = f'{args.name}/head-0'
        else:
            _head_args.name = f'head-0'

        return _head_args

    @property
    @abstractmethod
    def head_args(self) -> Namespace:
        """Get the arguments for the `head` of this BasePod.

        .. # noqa: DAR201
        """
        ...

    @abstractmethod
    def join(self):
        """Wait until all pods and peas exit."""
        ...

    @property
    @abstractmethod
    def _mermaid_str(self) -> List[str]:
        """String that will be used to represent the Pod graphically when `Flow.plot()` is invoked


        .. # noqa: DAR201
        """
        ...

    @property
    def deployments(self) -> List[Dict]:
        """Get deployments of the pod. The BasePod just gives one deployment.

        :return: list of deployments
        """
        return [
            {
                'name': self.name,
                'head_host': self.head_host,
                'head_port_in': self.head_port_in,
            }
        ]


class Pod(BasePod):
    """A Pod is an immutable set of peas, which run in replicas. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend. They can be also run in their own containers
    :param args: arguments parsed from the CLI
    :param needs: pod names of preceding pods, the output of these pods are going into the input of this pod
    """

    class _ReplicaSet:
        def __init__(
            self,
            pod_args: Namespace,
            args: List[Namespace],
            head_pea,
        ):
            self.pod_args = copy.copy(pod_args)
            self.args = args
            self.shard_id = args[0].shard_id
            self._peas = []
            self.head_pea = head_pea

        @property
        def is_ready(self):
            return all(p.is_ready.is_set() for p in self._peas)

        def clear_peas(self):
            self._peas.clear()

        @property
        def num_peas(self):
            return len(self._peas)

        def join(self):
            for pea in self._peas:
                pea.join()

        def wait_start_success(self):
            for pea in self._peas:
                pea.wait_start_success()

        async def rolling_update(self, uses_with: Optional[Dict] = None):
            # TODO make rolling_update robust, in what state this ReplicaSet ends when this fails?
            for i in range(len(self._peas)):
                _args = self.args[i]
                old_pea = self._peas[i]
                await GrpcConnectionPool.deactivate_worker(
                    worker_host=Pod.get_worker_host(_args, old_pea, self.head_pea),
                    worker_port=_args.port_in,
                    target_head=f'{self.head_pea.args.host}:{self.head_pea.args.port_in}',
                    shard_id=self.shard_id,
                )
                old_pea.close()
                _args.noblock_on_start = True
                _args.uses_with = uses_with
                new_pea = PeaFactory.build_pea(_args)
                new_pea.__enter__()
                await new_pea.async_wait_start_success()
                await GrpcConnectionPool.activate_worker(
                    worker_host=Pod.get_worker_host(_args, new_pea, self.head_pea),
                    worker_port=_args.port_in,
                    target_head=f'{self.head_pea.args.host}:{self.head_pea.args.port_in}',
                    shard_id=self.shard_id,
                )
                self.args[i] = _args
                self._peas[i] = new_pea

        async def _scale_up(self, replicas: int):
            new_peas = []
            new_args_list = []
            for i in range(len(self._peas), replicas):
                new_args = copy.copy(self.args[0])
                new_args.noblock_on_start = True
                new_args.name = new_args.name[:-1] + f'{i}'
                new_args.port_in = helper.random_port()
                new_args.replica_id = i
                # no exception should happen at create and enter time
                new_peas.append(PeaFactory.build_pea(new_args).start())
                new_args_list.append(new_args)
            exception = None
            for new_pea, new_args in zip(new_peas, new_args_list):
                try:
                    await new_pea.async_wait_start_success()
                    await GrpcConnectionPool.activate_worker(
                        worker_host=Pod.get_worker_host(
                            new_args, new_pea, self.head_pea
                        ),
                        worker_port=new_args.port_in,
                        target_head=f'{self.head_pea.args.host}:{self.head_pea.args.port_in}',
                        shard_id=self.shard_id,
                    )
                except (
                    RuntimeFailToStart,
                    TimeoutError,
                    RuntimeRunForeverEarlyError,
                ) as ex:
                    exception = ex
                    break

            if exception is not None:
                if self.pod_args.shards > 1:
                    msg = f' Scaling fails for shard {self.pod_args.shard_id}'
                else:
                    msg = ' Scaling fails'

                msg += f'due to executor failing to start with exception: {exception!r}'
                raise ScalingFails(msg)
            else:
                for new_pea, new_args in zip(new_peas, new_args_list):
                    self.args.append(new_args)
                    self._peas.append(new_pea)

        async def _scale_down(self, replicas: int):
            for i in reversed(range(replicas, len(self._peas))):
                # Close returns exception, but in theory `termination` should handle close properly
                try:
                    await GrpcConnectionPool.deactivate_worker(
                        worker_host=Pod.get_worker_host(
                            self.args[i], self._peas[i], self.head_pea
                        ),
                        worker_port=self.args[i].port_in,
                        target_head=f'{self.head_pea.args.host}:{self.head_pea.args.port_in}',
                        shard_id=self.shard_id,
                    )
                    self._peas[i].close()
                finally:
                    # If there is an exception at close time. Most likely the pea's terminated abruptly and therefore these
                    # peas are useless
                    del self._peas[i]
                    del self.args[i]

        async def scale(self, replicas: int):
            """
            Scale the amount of replicas of a given Executor.

            :param replicas: The number of replicas to scale to

                .. note: Scale is either successful or not. If one replica fails to start, the ReplicaSet remains in the same state
            """
            # TODO make scale robust, in what state this ReplicaSet ends when this fails?
            assert replicas > 0
            if replicas > len(self._peas):
                await self._scale_up(replicas)
            elif replicas < len(self._peas):
                await self._scale_down(
                    replicas
                )  # scale down has some challenges with the exit fifo
            self.pod_args.replicas = replicas

        @property
        def has_forked_processes(self):
            """
            Checks if any pea in this replica set is a forked process

            :returns: True if any Pea is a forked Process, False otherwise (Containers/JinaD)
            """
            for pea in self._peas:
                if type(pea) == Pea and pea.is_forked:
                    return True
            return False

        def __enter__(self):
            for _args in self.args:
                if getattr(self.pod_args, 'noblock_on_start', False):
                    _args.noblock_on_start = True
                if (
                    self.pod_args.replicas == 1
                ):  # keep backwards compatibility with `workspace` in `Executor`
                    _args.replica_id = -1
                self._peas.append(PeaFactory.build_pea(_args).start())
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            closing_exception = None
            for pea in self._peas:
                try:
                    pea.close()
                except Exception as exc:
                    if closing_exception is None:
                        closing_exception = exc
            if exc_val is None and closing_exception is not None:
                raise closing_exception

    def __init__(
        self, args: Union['Namespace', Dict], needs: Optional[Set[str]] = None
    ):
        super().__init__()
        args.upload_files = BasePod._set_upload_files(args)
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

        self.uses_before_pea = None
        self.uses_after_pea = None
        self.head_pea = None
        self.shards = {}
        self.update_pea_args()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.join()

    def update_pea_args(self):
        """ Update args of all its peas based on Pod args. Including head/tail"""
        if isinstance(self.args, Dict):
            # This is used when a Pod is created in a remote context, where peas & their connections are already given.
            self.peas_args = self.args
        else:
            self.peas_args = self._parse_args(self.args)

    def update_worker_pea_args(self):
        """ Update args of all its worker peas based on Pod args. Does not touch head and tail"""
        self.peas_args['peas'] = self._set_peas_args(self.args)

    @property
    def first_pea_args(self) -> Namespace:
        """Return the first worker pea's args


        .. # noqa: DAR201
        """
        # note this will be never out of boundary
        return self.peas_args['peas'][0][0]

    @property
    def host(self) -> str:
        """Get the host name of this Pod


        .. # noqa: DAR201
        """
        return self.first_pea_args.host

    def _parse_args(
        self, args: Namespace
    ) -> Dict[str, Optional[Union[List[Namespace], Namespace]]]:
        return self._parse_base_pod_args(args)

    @property
    def head_args(self) -> Namespace:
        """Get the arguments for the `head` of this Pod.


        .. # noqa: DAR201
        """
        return self.peas_args['head']

    @head_args.setter
    def head_args(self, args):
        """Set the arguments for the `head` of this Pod.


        .. # noqa: DAR101
        """
        self.peas_args['head'] = args

    @property
    def uses_before_args(self) -> Namespace:
        """Get the arguments for the `uses_before` of this Pod.


        .. # noqa: DAR201
        """
        return self.peas_args['uses_before']

    @uses_before_args.setter
    def uses_before_args(self, args):
        """Set the arguments for the `uses_before` of this Pod.


        .. # noqa: DAR101
        """
        self.peas_args['uses_before'] = args

    @property
    def uses_after_args(self) -> Namespace:
        """Get the arguments for the `uses_after` of this Pod.


        .. # noqa: DAR201
        """
        return self.peas_args['uses_after']

    @uses_after_args.setter
    def uses_after_args(self, args):
        """Set the arguments for the `uses_after` of this Pod.


        .. # noqa: DAR101
        """
        self.peas_args['uses_after'] = args

    @property
    def all_args(self) -> List[Namespace]:
        """Get all arguments of all Peas in this BasePod.

        .. # noqa: DAR201
        """
        all_args = (
            ([self.peas_args['uses_before']] if self.peas_args['uses_before'] else [])
            + ([self.peas_args['uses_after']] if self.peas_args['uses_after'] else [])
            + ([self.peas_args['head']] if self.peas_args['head'] else [])
        )
        for shard_id in self.peas_args['peas']:
            all_args += self.peas_args['peas'][shard_id]
        return all_args

    @property
    def num_peas(self) -> int:
        """Get the number of running :class:`Pea`

        .. # noqa: DAR201
        """
        num_peas = 0
        if self.head_pea is not None:
            num_peas += 1
        if self.uses_before_pea is not None:
            num_peas += 1
        if self.uses_after_pea is not None:
            num_peas += 1
        if self.shards:  # external pods
            for shard_id in self.shards:
                num_peas += self.shards[shard_id].num_peas
        return num_peas

    def __eq__(self, other: 'BasePod'):
        return self.num_peas == other.num_peas and self.name == other.name

    def activate(self):
        """
        Activate all worker peas in this pod by registering them with the head
        """
        if self.head_pea is not None:
            for shard_id in self.peas_args['peas']:
                for pea_idx, pea_args in enumerate(self.peas_args['peas'][shard_id]):
                    worker_host = self.get_worker_host(
                        pea_args, self.shards[shard_id]._peas[pea_idx], self.head_pea
                    )
                    GrpcConnectionPool.activate_worker_sync(
                        worker_host,
                        int(pea_args.port_in),
                        self.head_pea.runtime_ctrl_address,
                        shard_id,
                    )

    @staticmethod
    def get_worker_host(pea_args, pea, head_pea):
        """
        Check if the current pea and head are both containerized on the same host
        If so __docker_host__ needs to be advertised as the worker's address to the head

        :param pea_args: arguments of the worker pea
        :param pea: the worker pea
        :param head_pea: head pea communicating with the worker pea
        :return: host to use in activate messages
        """
        # Check if the current pea and head are both containerized on the same host
        # If so __docker_host__ needs to be advertised as the worker's address to the head
        worker_host = (
            __docker_host__
            if Pod._is_container_to_container(pea, head_pea)
            and host_is_local(pea_args.host)
            else pea_args.host
        )
        return worker_host

    @staticmethod
    def _is_container_to_container(pea, head_pea):
        def _in_docker():
            path = '/proc/self/cgroup'
            return (
                os.path.exists('/.dockerenv')
                or os.path.isfile(path)
                and any('docker' in line for line in open(path))
            )

        # Check if both shard_id/pea_idx and the head are containerized
        # if the head is not containerized, it still could mean that the pod itself is containerized
        return (type(pea) == ContainerPea or type(pea) == JinaDPea) and (
            type(head_pea) == ContainerPea or type(head_pea) == JinaDPea or _in_docker()
        )

    def start(self) -> 'Pod':
        """
        Start to run all :class:`Pea` in this BasePod.

        :return: started pod

        .. note::
            If one of the :class:`Pea` fails to start, make sure that all of them
            are properly closed.
        """
        if self.peas_args['uses_before'] is not None:
            _args = self.peas_args['uses_before']
            if getattr(self.args, 'noblock_on_start', False):
                _args.noblock_on_start = True
            self.uses_before_pea = PeaFactory.build_pea(_args)
            self.enter_context(self.uses_before_pea)
        if self.peas_args['uses_after'] is not None:
            _args = self.peas_args['uses_after']
            if getattr(self.args, 'noblock_on_start', False):
                _args.noblock_on_start = True
            self.uses_after_pea = PeaFactory.build_pea(_args)
            self.enter_context(self.uses_after_pea)
        if self.peas_args['head'] is not None:
            _args = self.peas_args['head']
            if getattr(self.args, 'noblock_on_start', False):
                _args.noblock_on_start = True
            self.head_pea = PeaFactory.build_pea(_args)
            self.enter_context(self.head_pea)
        for shard_id in self.peas_args['peas']:
            self.shards[shard_id] = self._ReplicaSet(
                self.args,
                self.peas_args['peas'][shard_id],
                self.head_pea,
            )
            self.enter_context(self.shards[shard_id])

        if not getattr(self.args, 'noblock_on_start', False):
            self.activate()
        return self

    def wait_start_success(self) -> None:
        """Block until all peas starts successfully.

        If not successful, it will raise an error hoping the outer function to catch it
        """
        if not self.args.noblock_on_start:
            raise ValueError(
                f'{self.wait_start_success!r} should only be called when `noblock_on_start` is set to True'
            )
        try:
            if self.uses_before_pea is not None:
                self.uses_before_pea.wait_start_success()
            if self.uses_after_pea is not None:
                self.uses_after_pea.wait_start_success()
            if self.head_pea is not None:
                self.head_pea.wait_start_success()
            for shard_id in self.shards:
                self.shards[shard_id].wait_start_success()
            self.activate()
        except:
            self.close()
            raise

    def join(self):
        """Wait until all peas exit"""
        try:
            if self.uses_before_pea is not None:
                self.uses_before_pea.join()
            if self.uses_after_pea is not None:
                self.uses_after_pea.join()
            if self.head_pea is not None:
                self.head_pea.join()
            if self.shards:
                for shard_id in self.shards:
                    self.shards[shard_id].join()
        except KeyboardInterrupt:
            pass
        finally:
            self.head_pea = None
            if self.shards:
                for shard_id in self.shards:
                    self.shards[shard_id].clear_peas()

    @property
    def is_ready(self) -> bool:
        """Checks if Pod is ready

        .. note::
            A Pod is ready when all the Peas it contains are ready


        .. # noqa: DAR201
        """
        is_ready = True
        if self.head_pea is not None:
            is_ready = self.head_pea.is_ready.is_set()
        if is_ready:
            for shard_id in self.shards:
                is_ready = self.shards[shard_id].is_ready
        if is_ready and self.uses_before_pea is not None:
            is_ready = self.uses_before_pea.is_ready.is_set()
        if is_ready and self.uses_after_pea is not None:
            is_ready = self.uses_after_pea.is_ready.is_set()
        return is_ready

    @property
    def _has_forked_processes(self):
        return any(
            [self.shards[shard_id].has_forked_processes for shard_id in self.shards]
        )

    async def rolling_update(self, uses_with: Optional[Dict] = None):
        """Reload all Peas of this Pod.

        :param uses_with: a Dictionary of arguments to restart the executor with
        """
        tasks = []
        try:
            import asyncio

            for shard_id in self.shards:
                task = asyncio.create_task(
                    self.shards[shard_id].rolling_update(uses_with=uses_with)
                )
                # it is dangerous to fork new processes (peas) while grpc operations are ongoing
                # while we use fork, we need to guarantee that forking/grpc status checking is done sequentially
                # this is true at least when the flow process and the forked processes are running in the same OS
                # thus this does not apply to K8s
                # to ContainerPea it still applies due to the managing process being forked
                # source: https://grpc.github.io/grpc/cpp/impl_2codegen_2fork_8h.html#a450c01a1187f69112a22058bf690e2a0
                await task
                tasks.append(task)

            await asyncio.gather(*tasks)
        except:
            for task in tasks:
                if not task.done():
                    task.cancel()

    async def scale(self, replicas: int):
        """
        Scale the amount of replicas of a given Executor.

        :param replicas: The number of replicas to scale to
        """
        self.args.replicas = replicas

        tasks = []
        try:
            import asyncio

            for shard_id in self.shards:
                task = asyncio.create_task(
                    self.shards[shard_id].scale(replicas=replicas)
                )
                # see rolling_update for explanation of sequential excution
                await task
                tasks.append(task)

            await asyncio.gather(*tasks)
        except:
            # TODO: Handle the failure of one of the shards. Unscale back all of them to the original state? Cancelling would potentially be dangerous.
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise

    @staticmethod
    def _set_peas_args(args: Namespace) -> Dict[int, List[Namespace]]:
        result = {}
        _host_list = (
            args.peas_hosts
            if hasattr(args, 'peas_hosts') and args.peas_hosts
            else [
                args.host,
            ]
        )

        sharding_enabled = args.shards and args.shards > 1
        for shard_id in range(args.shards):
            replica_args = []
            for idx, pea_host in zip(range(args.replicas), cycle(_host_list)):
                _args = copy.deepcopy(args)
                _args.shard_id = shard_id
                _args.replica_id = idx
                _args.pea_role = PeaRoleType.WORKER
                _args.identity = random_identity()

                _args.host = pea_host
                if _args.name:
                    _args.name += (
                        f'/shard-{shard_id}/rep-{idx}'
                        if sharding_enabled
                        else f'/rep-{idx}'
                    )
                else:
                    _args.name = f'{idx}'

                _args.port_in = helper.random_port()

                # pea workspace if not set then derive from workspace
                if not _args.workspace:
                    _args.workspace = args.workspace
                replica_args.append(_args)
            result[shard_id] = replica_args
        return result

    @staticmethod
    def _set_uses_before_after_args(args: Namespace, entity_type: str) -> Namespace:

        _args = copy.deepcopy(args)
        _args.pea_role = PeaRoleType.WORKER
        _args.identity = random_identity()
        _args.host = __default_host__
        _args.port_in = helper.random_port()

        if _args.name:
            _args.name += f'/{entity_type}-0'
        else:
            _args.name = f'{entity_type}-0'

        if 'uses_before' == entity_type:
            _args.uses = args.uses_before or __default_executor__
        elif 'uses_after' == entity_type:
            _args.uses = args.uses_after or __default_executor__
        else:
            raise ValueError(
                f'uses_before/uses_after pea does not support type {entity_type}'
            )

        # pea workspace if not set then derive from workspace
        if not _args.workspace:
            _args.workspace = args.workspace
        return _args

    def _parse_base_pod_args(self, args):
        parsed_args = {
            'head': None,
            'uses_before': None,
            'uses_after': None,
            'peas': {},
        }

        # a gateway has no heads and uses
        if self.role != PodRoleType.GATEWAY:
            if (
                getattr(args, 'uses_before', None)
                and args.uses_before != __default_executor__
            ):
                uses_before_args = self._set_uses_before_after_args(
                    args, entity_type='uses_before'
                )
                parsed_args['uses_before'] = uses_before_args
                args.uses_before_address = (
                    f'{uses_before_args.host}:{uses_before_args.port_in}'
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
                    f'{uses_after_args.host}:{uses_after_args.port_in}'
                )

            parsed_args['head'] = BasePod._copy_to_head_args(args)
        parsed_args['peas'] = self._set_peas_args(args)

        return parsed_args

    @property
    def _mermaid_str(self) -> List[str]:
        """String that will be used to represent the Pod graphically when `Flow.plot()` is invoked.
        It does not include used_before/uses_after


        .. # noqa: DAR201
        """
        mermaid_graph = []
        if self.role != PodRoleType.GATEWAY and not getattr(
            self.args, 'external', False
        ):
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
            if len(self.peas_args['peas']) > 1:
                # multiple shards
                for shard_id, peas_args in self.peas_args['peas'].items():
                    shard_name = f'{self.name}/shard-{shard_id}'
                    shard_names.append(shard_name)
                    shard_mermaid_graph = [
                        f'subgraph {shard_name};',
                        f'\ndirection TB;\n',
                    ]
                    names = [
                        args.name for args in peas_args
                    ]  # all the names of each of the replicas
                    uses = [
                        args.uses for args in peas_args
                    ]  # all the uses should be the same but let's keep it this
                    # way
                    for rep_i, (name, use) in enumerate(zip(names, uses)):
                        shard_mermaid_graph.append(f'{name}[{use}]:::PEA;')
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
                # single shard case
                names = [
                    args.name for args in self.peas_args['peas'][0]
                ]  # all the names of each of the replicas
                uses = [
                    args.uses for args in self.peas_args['peas'][0]
                ]  # all the uses should be the same but let's keep it this way
                if uses_before_name is None and uses_after_name is None:
                    # just put the replicas in parallel
                    for rep_i, (name, use) in enumerate(zip(names, uses)):
                        mermaid_graph.append(f'{name}/rep-{rep_i}[{use}]:::PEA;')
                if uses_before_name is not None:
                    for name, use in zip(names, uses):
                        mermaid_graph.append(
                            f'{self.args.name}-head[{uses_before_uses}]:::HEADTAIL --> {name}[{use}]:::PEA;'
                        )
                if uses_after_name is not None:
                    for name, use in zip(names, uses):
                        mermaid_graph.append(
                            f'{name}[{use}]:::PEA --> {self.args.name}-tail[{uses_after_uses}]:::HEADTAIL;'
                        )
            mermaid_graph.append('end;')
        return mermaid_graph
