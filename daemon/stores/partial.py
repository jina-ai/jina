from argparse import Namespace
from typing import Optional

from jina import Flow
from jina.peapods import Pea, Pod
from jina.helper import colored
from jina.logging.logger import JinaLogger

from .. import jinad_args
from ..models import DaemonID
from ..models.enums import UpdateOperation
from ..models.partial import PartialFlowItem, PartialStoreItem, PartialStoreStatus


class PartialStore:
    _status_model = PartialStoreStatus

    def __init__(self):
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))
        self.status = self.__class__._status_model()

    def add(self, *args, **kwargs):
        """Add a new element to the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError

    def update(self, *args, **kwargs):
        """Updates the element to the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        """Deletes an element from the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError


class PartialPeaStore(PartialStore):
    peapod_cls = Pea
    _status_model = PartialStoreStatus

    def add(self, args: Namespace, **kwargs) -> 'DaemonID':
        try:
            _id = args.identity
            self.object = self.peapod_cls(args).start()
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.status.items = PartialStoreItem(
                arguments=vars(args)
            )
            self._logger.success(
                f'{colored(_id, "cyan")} is created'
            )
            return _id

    def delete(self):
        self.object.close()


class PartialPodStore(PartialPeaStore):
    peapod_cls = Pod

    def update(self):
        # TODO
        pass


class PartialFlowStore(PartialStore):
    _kind = 'flow'
    _status_model = PartialStoreStatus

    def add(
        self, filename: str, id: DaemonID, port_expose: Optional[int]
    ) -> 'DaemonID':
        try:
            with open(filename) as f:
                y_spec = f.read()
            self.flow: Flow = Flow.load_config(y_spec)
            self.flow.identity = id.jid
            self.flow.workspace_id = jinad_args.workspace_id
            # If port_expose is not defined in yaml source and passed by main jinad
            self._logger.critical(port_expose)
            if 'port_expose' not in self.flow._common_kwargs and port_expose:
                self.flow._common_kwargs['port_expose'] = port_expose
            self._logger.critical(self.flow._common_kwargs['port_expose'])
            self.flow.start()
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self.status.items = PartialFlowItem(
                arguments=vars(self.flow.args),
                yaml_source=y_spec
            )
            self._logger.success(f'{colored(id, "cyan")} is created')
            return id

    def update(self, kind, dump_path, pod_name, shards):
        if kind == UpdateOperation.ROLLING_UPDATE:
            self.flow.rolling_update(pod_name=pod_name, dump_path=dump_path)
        elif kind == UpdateOperation.DUMP:
            raise NotImplementedError(
                f' sending post request does not work because asyncio loop is occupied'
            )

    def delete(self):
        self.flow.close()
