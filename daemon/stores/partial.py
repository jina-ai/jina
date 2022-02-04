from pathlib import Path
from abc import ABC, abstractmethod
from argparse import Namespace
from typing import Dict, Optional, Type, Union

from jina.helper import colored, random_port
from jina.orchestrate.deployments import Deployment, BaseDeployment
from jina.orchestrate.pods.factory import PodFactory
from jina.orchestrate.pods import BasePod
from jina.orchestrate.pods.helper import update_runtime_cls
from jina import Flow, __docker_host__
from jina.logging.logger import JinaLogger

from daemon import jinad_args, __partial_workspace__
from daemon.models.ports import Ports, PortMappings
from daemon.models.partial import PartialFlowItem, PartialStoreItem


class PartialStore(ABC):
    """A store spawned inside partial-daemon container"""

    def __init__(self):
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))
        self.item = PartialStoreItem()
        self.object: Union[Type['BasePod'], Type['BaseDeployment'], 'Flow'] = None

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
                self._logger.info(self.item.arguments)
                if self.item.arguments.get('identity'):
                    self._logger.success(
                        f'{colored(self.item.arguments["identity"], "cyan")} is removed!'
                    )
                else:
                    self._logger.success('object is removed!')
            else:
                self._logger.warning(f'nothing to close. exiting')
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item = PartialStoreItem()


class PartialPodStore(PartialStore):
    """A Pod store spawned inside partial-daemon container"""

    poddeployment_constructor = PodFactory.build_pod

    def add(
        self, args: Namespace, envs: Optional[Dict] = {}, **kwargs
    ) -> PartialStoreItem:
        """Starts a Pod in `partial-daemon`

        :param args: namespace args for the pod/deployment
        :param envs: environment variables to be passed into partial pod/deployment
        :param kwargs: keyword args
        :return: Item describing the Pod object
        """
        try:
            # This is set so that ContainerRuntime sets host_ctrl to __docker_host__
            # and on linux machines, we can access dockerhost inside containers
            if args.runtime_cls == 'ContainerRuntime':
                args.docker_kwargs = {'extra_hosts': {__docker_host__: 'host-gateway'}}
            self.object: Union[
                Type['BasePod'], Type['BaseDeployment']
            ] = self.__class__.poddeployment_constructor(args).__enter__()
            self.object.env = envs
        except Exception as e:
            if hasattr(self, 'object') and self.object:
                self.object.__exit__(type(e), e, e.__traceback__)
            self._logger.error(f'{e!r}')

            raise
        else:
            self.item = PartialStoreItem(arguments=vars(args))
            self._logger.success(f'{colored(args.name, "cyan")} is created!')
            return self.item


class PartialDeploymentStore(PartialPodStore):
    """A Deployment store spawned inside partial-daemon container"""

    poddeployment_constructor = Deployment

    async def rolling_update(
        self, uses_with: Optional[Dict] = None
    ) -> PartialStoreItem:
        """Perform rolling_update on current Deployment

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
            self._logger.success(f'Deployment is successfully rolling_updated!')
            return self.item

    async def scale(self, replicas: int) -> PartialStoreItem:
        """Scale the current Deployment
        :param replicas: number of replicas for the Deployment
        :return: Item describing the Flow object
        """
        try:
            await self.object.scale(replicas=replicas)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item.arguments = vars(self.object.args)
            self._logger.success(f'Deployment is successfully scaled!')
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

            for deployment in self.object._deployment_nodes.values():
                runtime_cls = update_runtime_cls(deployment.args, copy=True).runtime_cls
                if port_mapping and (
                    hasattr(deployment.args, 'replicas')
                    and deployment.args.replicas > 1
                ):
                    for pod_args in [deployment.pod_args['head']]:
                        if pod_args.name in port_mapping.pod_names:
                            for port_name in Ports.__fields__:
                                self._set_pod_ports(pod_args, port_mapping, port_name)
                    deployment.update_worker_pod_args()

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

    def _set_pod_ports(self, pod_args, port_mapping, port_name):
        if hasattr(pod_args, port_name):
            setattr(
                pod_args,
                port_name,
                getattr(
                    port_mapping[pod_args.name].ports,
                    port_name,
                    random_port(),
                ),
            )

    async def rolling_update(
        self, deployment_name: str, uses_with: Optional[Dict] = None
    ) -> PartialFlowItem:
        """Perform rolling_update on the Deployment in current Flow

        :param deployment_name: Deployment in the Flow to be rolling updated
        :param uses_with: a Dictionary of arguments to restart the executor with
        :return: Item describing the Flow object
        """
        try:
            await self._rolling_update(
                deployment_name=deployment_name, uses_with=uses_with
            )
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item.arguments = vars(self.object.args)
            self._logger.success(f'Flow is successfully rolling_updated!')
            return self.item

    async def _rolling_update(
        self,
        deployment_name: str,
        uses_with: Optional[Dict] = None,
    ):
        """
        Reload all replicas of a deployment sequentially

        :param deployment_name: deployment to update
        :param uses_with: a Dictionary of arguments to restart the executor with
        """
        await self.object._deployment_nodes[deployment_name].rolling_update(
            uses_with=uses_with
        )

    async def scale(self, deployment_name: str, replicas: int) -> PartialFlowItem:
        """Scale the Deployment in current Flow
        :param deployment_name: Deployment to be scaled
        :param replicas: number of replicas for the Deployment
        :return: Item describing the Flow object
        """
        try:
            await self._scale(deployment_name=deployment_name, replicas=replicas)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        self.item.arguments = vars(self.object.args)
        self._logger.success(f'Flow is successfully scaled!')
        return self.item

    async def _scale(
        self,
        deployment_name: str,
        replicas: int,
    ):
        """
        Scale the amount of replicas of a given Executor.
        :param deployment_name: deployment to update
        :param replicas: The number of replicas to scale to
        """

        await self.object._deployment_nodes[deployment_name].scale(replicas)
