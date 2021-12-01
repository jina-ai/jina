from pathlib import Path
from abc import ABC, abstractmethod
from argparse import Namespace
from typing import Dict, Optional, Union

from jina.helper import colored, random_port
from jina.peapods import Pea, Pod, CompoundPod
from jina.peapods.peas.helper import update_runtime_cls
from jina import Flow, __docker_host__
from jina.logging.logger import JinaLogger

from .. import jinad_args, __partial_workspace__
from ..models import GATEWAY_RUNTIME_DICT
from ..models.ports import Ports, PortMappings
from ..models.partial import PartialFlowItem, PartialStoreItem


class PartialStore(ABC):
    """A store spawned inside partial-daemon container"""

    def __init__(self):
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))
        self.item = PartialStoreItem()
        self.object: Union['Pea', 'Pod', 'Flow'] = None

    @abstractmethod
    def add(self, *args, **kwargs) -> PartialStoreItem:
        """Add a new element to the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        ...

    def delete(self) -> None:
        """Terminates the object in the store & stops the server"""
        try:
            if hasattr(self.object, 'close'):
                self.object.close()
            else:
                self._logger.warning(f'nothing to close. exiting')
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise


class PartialPeaStore(PartialStore):
    """A Pea store spawned inside partial-daemon container"""

    peapod_cls = Pea

    def add(
        self, args: Namespace, envs: Optional[Dict] = {}, **kwargs
    ) -> PartialStoreItem:
        """Starts a Pea in `partial-daemon`

        :param args: namespace args for the pea/pod
        :param envs: environment variables to be passed into partial pea/pod
        :param kwargs: keyword args
        :return: Item describing the Pea object
        """
        try:
            _id = args.identity
            # This is set so that ContainerRuntime sets host_ctrl to __docker_host__
            # and on linux machines, we can access dockerhost inside containers
            if args.runtime_cls == 'ContainerRuntime':
                args.docker_kwargs = {'extra_hosts': {__docker_host__: 'host-gateway'}}
            self.object: Union['Pea', 'Pod'] = self.peapod_cls(args).__enter__()
            self.object.env = envs
        except Exception as e:
            if hasattr(self, 'object'):
                self.object.__exit__(type(e), e, e.__traceback__)
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item = PartialStoreItem(arguments=vars(args))
            self._logger.success(f'{colored(_id, "cyan")} is created')
            return self.item


class PartialPodStore(PartialPeaStore):
    """A Pod store spawned inside partial-daemon container"""

    peapod_cls = Pod

    async def rolling_update(
        self, uses_with: Optional[Dict] = None
    ) -> PartialStoreItem:
        """Perform rolling_update on current Pod

        :param uses_with: a Dictionary of arguments to restart the executor with
        :return: Item describing the Flow object
        """
        try:
            await self.object.rolling_update(uses_with=uses_with)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item.arguments = vars(self.object.args)
            self._logger.success(f'Pod is successfully rolling_updated!')
            return self.item

    async def scale(self, replicas: int) -> PartialStoreItem:
        """Scale the current Pod

        :param replicas: number of replicas for the Pod
        :return: Item describing the Flow object
        """
        try:
            await self.object.scale(replicas=replicas)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item.arguments = vars(self.object.args)
            self._logger.success(f'Pod is successfully scaled!')
            return self.item


class PartialFlowStore(PartialStore):
    """A Flow store spawned inside partial-daemon container"""

    def add(
        self,
        args: Namespace,
        port_mapping: Optional[PortMappings] = None,
        envs: Optional[Dict] = {},
        **kwargs,
    ) -> PartialStoreItem:
        """Starts a Flow in `partial-daemon`.

        :param args: namespace args for the flow
        :param port_mapping: ports to be set
        :param envs: environment variables to be passed into partial flow
        :param kwargs: keyword args
        :return: Item describing the Flow object
        """
        try:
            if not args.uses:
                raise ValueError('uses yaml file was not specified in flow definition')
            elif not Path(args.uses).is_file():
                raise ValueError(f'uses {args.uses} not found in workspace')

            self.object: Flow = Flow.load_config(args.uses).build()
            self.object.workspace_id = jinad_args.workspace_id
            self.object.workspace = __partial_workspace__
            self.object.env = {'HOME': __partial_workspace__, **envs}

            for pod in self.object._pod_nodes.values():
                runtime_cls = update_runtime_cls(pod.args, copy=True).runtime_cls
                if isinstance(pod, CompoundPod):
                    # In dependencies, we set `runs_in_docker` for the `gateway` and for `CompoundPod` we need
                    # `runs_in_docker` to be False. Since `Flow` args are sent to all Pods, `runs_in_docker` gets set
                    # for the `CompoundPod`, which blocks the requests. Below we unset that (hacky & ugly).
                    # We do it only for runtimes that starts on local (not container or remote)
                    if (
                        runtime_cls
                        in [
                            'ZEDRuntime',
                            'GRPCDataRuntime',
                            'ContainerRuntime',
                        ]
                        + list(GATEWAY_RUNTIME_DICT.values())
                    ):
                        pod.args.runs_in_docker = False
                        for shards_args in pod.shards_args:
                            shards_args.runs_in_docker = False
                        if port_mapping:
                            # Ports for Head & Tail Peas in a CompoundPod set here.
                            # This is specifically needed as `save_config` doesn't save `port_out` for a HeadPea
                            # and `port_in` for a TailPea, which might be useful if replicas and head/tail Peas
                            # are in different containers.
                            for pea_args in [pod.head_args, pod.tail_args]:
                                if pea_args.name in port_mapping.pea_names:
                                    for port_name in Ports.__fields__:
                                        self._set_pea_ports(
                                            pea_args, port_mapping, port_name
                                        )
                            # Update shard_args according to updated head & tail args
                            pod.assign_shards()
                else:
                    if port_mapping and (
                        hasattr(pod.args, 'replicas') and pod.args.replicas > 1
                    ):
                        for pea_args in [pod.peas_args['head'], pod.peas_args['tail']]:
                            if pea_args.name in port_mapping.pea_names:
                                for port_name in Ports.__fields__:
                                    self._set_pea_ports(
                                        pea_args, port_mapping, port_name
                                    )
                        pod.update_worker_pea_args()

                    # avoid setting runs_in_docker for Pods with parallel > 1 and using `ZEDRuntime`
                    # else, replica-peas would try connecting to head/tail-pea via __docker_host__
                    if runtime_cls in ['ZEDRuntime', 'GRPCDataRuntime'] and (
                        hasattr(pod.args, 'replicas') and pod.args.replicas > 1
                    ):
                        pod.args.runs_in_docker = False
                        pod.update_worker_pea_args()

            self.object = self.object.__enter__()
        except Exception as e:
            if hasattr(self, 'object'):
                self.object.__exit__(type(e), e, e.__traceback__)
            self._logger.error(f'{e!r}')
            raise
        else:
            with open(args.uses) as yaml_file:
                yaml_source = yaml_file.read()

            self.item = PartialFlowItem(
                arguments={
                    'port_expose': self.object.port_expose,
                    'protocol': self.object.protocol.name,
                    **vars(self.object.args),
                },
                yaml_source=yaml_source,
            )
            self._logger.success(f'Flow is created successfully!')
            return self.item

    def _set_pea_ports(self, pea_args, port_mapping, port_name):
        if hasattr(pea_args, port_name):
            setattr(
                pea_args,
                port_name,
                getattr(
                    port_mapping[pea_args.name].ports,
                    port_name,
                    random_port(),
                ),
            )

    def rolling_update(
        self, pod_name: str, uses_with: Optional[Dict] = None
    ) -> PartialFlowItem:
        """Perform rolling_update on the Pod in current Flow

        :param pod_name: Pod in the Flow to be rolling updated
        :param uses_with: a Dictionary of arguments to restart the executor with
        :return: Item describing the Flow object
        """
        try:
            self.object.rolling_update(pod_name=pod_name, uses_with=uses_with)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item.arguments = vars(self.object.args)
            self._logger.success(f'Flow is successfully rolling_updated!')
            return self.item

    def scale(self, pod_name: str, replicas: int) -> PartialFlowItem:
        """Scale the Pod in current Flow

        :param pod_name: Pod to be scaled
        :param replicas: number of replicas for the Pod
        :return: Item describing the Flow object
        """
        try:
            self.object.scale(pod_name=pod_name, replicas=replicas)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item.arguments = vars(self.object.args)
            self._logger.success(f'Flow is successfully scaled!')
            return self.item
