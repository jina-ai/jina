from argparse import Namespace
from typing import Union

from jina.helper import colored
from jina.peapods import Pea, Pod
from jina import Flow, __docker_host__
from jina.logging.logger import JinaLogger

from .. import jinad_args
from ..models.enums import UpdateOperation
from ..models.partial import PartialFlowItem, PartialStoreItem


class PartialStore:
    """A store spawned inside mini-jinad container"""

    def __init__(self):
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))
        self.item = PartialStoreItem()

    def add(self, *args, **kwargs) -> PartialStoreItem:
        """Add a new element to the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError

    def update(self, *args, **kwargs) -> PartialStoreItem:
        """Updates the element to the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError

    def delete(self) -> None:
        """Terminates the object in the store & stops the server"""
        try:
            if hasattr(self, 'object'):
                self.object.close()
            else:
                self._logger.warning(f'nothing to close. exiting')
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise


class PartialPeaStore(PartialStore):
    """A Pea store spawned inside mini-jinad container"""

    peapod_cls = Pea

    def add(self, args: Namespace, **kwargs) -> PartialStoreItem:
        """Starts a Pea in `mini-jinad`

        :param args: namespace args for the pea/pod
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
    """A Pod store spawned inside mini-jinad container"""

    peapod_cls = Pod


class PartialFlowStore(PartialStore):
    """A Flow store spawned inside mini-jinad container"""

    def add(self, args: Namespace, port_expose: int, **kwargs) -> PartialStoreItem:
        """Starts a Flow in `mini-jinad`.

        :param args: namespace args for the flow
        :param port_expose: port expose for the Flow
        :param kwargs: keyword args
        :return: Item describing the Flow object
        """
        try:
            if not args.uses:
                raise ValueError('Uses yaml file was not specified in flow definition')

            with open(args.uses) as yaml_file:
                y_spec = yaml_file.read()
            flow = Flow.load_config(y_spec)
            flow.workspace_id = jinad_args.workspace_id
            flow.port_expose = port_expose
            self.object: Flow = flow
            self.object = self.object.__enter__()
        except Exception as e:
            if hasattr(self, 'object'):
                self.object.__exit__(type(e), e, e.__traceback__)
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item = PartialFlowItem(
                arguments={
                    'port_expose': self.object.port_expose,
                    **vars(self.object.args),
                },
                yaml_source=y_spec,
            )
            self._logger.success(f'Flow is created')
            return self.item

    def update(
        self,
        kind: UpdateOperation,
        dump_path: str,
        pod_name: str,
        shards: int,
        **kwargs,
    ) -> PartialFlowItem:
        """Runs an update operation on the Flow.
        :param kind: type of update command to execute (dump/rolling_update)
        :param dump_path: the path to which to dump on disk
        :param pod_name: pod to target with the dump request
        :param shards: nr of shards to dump
        :param kwargs: keyword args
        :return: Item describing the Flow object
        """
        try:
            if kind == UpdateOperation.ROLLING_UPDATE:
                self.object.rolling_update(pod_name=pod_name, dump_path=dump_path)
            else:
                self._logger.error(f'unsupoorted kind: {kind}, no changes done')
                return self.item
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item.arguments = vars(self.object.args)
            return self.item
