from argparse import Namespace

from jina import Flow
from jina.peapods import Pea, Pod
from jina.helper import colored
from jina.logging.logger import JinaLogger

from ..models import DaemonID
from .. import jinad_args, __dockerhost__
from ..models.enums import UpdateOperation
from ..models.partial import PartialFlowItem, PartialStoreItem


class PartialStore:
    """
    `mini-jinad` should always be managed by jinad & not by the user.
    PartialStore creates Flows/Pods/Peas inside `mini-jinad`.
    """

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
        """Deletes an element from the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError


class PartialPeaStore(PartialStore):
    peapod_cls = Pea

    def add(self, args: Namespace, **kwargs) -> PartialStoreItem:
        """Starts a Pea in `mini-jinad`

        :return: Item describing the Pea object
        """
        try:
            _id = args.identity
            # This is set so that ContainerRuntime sets host_ctrl to __dockerhost__
            # and on linux machines, we can access dockerhost inside containers
            args.docker_kwargs = {'extra_hosts': {__dockerhost__: 'host-gateway'}}
            self.object = self.peapod_cls(args).start()
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item = PartialStoreItem(arguments=vars(args))
            self._logger.success(f'{colored(_id, "cyan")} is created')
            return self.item

    def update(self) -> PartialStoreItem:
        # TODO
        pass

    def delete(self) -> None:
        """Terminates a Pea in `mini-jinad`"""
        self.object.close()


class PartialPodStore(PartialPeaStore):
    peapod_cls = Pod


class PartialFlowStore(PartialStore):
    def add(self, filename: str, id: DaemonID, port_expose: int) -> PartialStoreItem:
        """Starts a Flow in `mini-jinad`.

        :return: Item describing the Flow object
        """
        try:
            with open(filename) as f:
                y_spec = f.read()
            self.object: Flow = Flow.load_config(y_spec)
            self.object.identity = id.jid
            self.object.workspace_id = jinad_args.workspace_id
            # Main jinad sets Flow's port_expose so that it is exposed before starting the container.
            self.object.args.port_expose = port_expose
            self.object.start()
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item = PartialFlowItem(
                arguments=vars(self.object.args), yaml_source=y_spec
            )
            self._logger.success(f'{colored(id, "cyan")} is created')
            return self.item

    def update(self, kind, dump_path, pod_name, shards, **kwargs) -> PartialFlowItem:
        try:
            if kind == UpdateOperation.ROLLING_UPDATE:
                self.object.rolling_update(pod_name=pod_name, dump_path=dump_path)
            elif kind == UpdateOperation.DUMP:
                raise NotImplementedError(
                    f' sending post request does not work because asyncio loop is occupied'
                )
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item.arguments = vars(self.object.args)
            return self.item

    def delete(self) -> None:
        try:
            self.object.close()
            # Server should exit here
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.item = PartialStoreItem()
