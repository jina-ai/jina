from daemon.models.base import StoreStatus, StoreItem
from daemon.stores.base import BaseStore
from jina import Flow
from jina.parsers import set_pod_parser, set_pea_parser
from jina.parsers.flow import set_flow_parser
from jina.peapods.peas import BasePea
from jina.peapods.pods.factory import PodFactory
from jina.peapods.runtimes import ZEDRuntime


class PartialStoreStatus(StoreStatus):
    items: StoreItem = StoreItem()

    def __len__(self):
        return 1


class PeaStore(BaseStore):
    _kind = 'pea'
    _status_model = PartialStoreStatus

    def __init__(self, args) -> object:
        super().__init__()
        self.pea = BasePea(set_pea_parser().parse_args(args))
        self.pea.runtime_cls = ZEDRuntime
        self.pea.start()


class PodStore(BaseStore):
    _kind = 'pod'
    _status_model = PartialStoreStatus

    def __init__(self, args):
        super().__init__()
        self.pod = PodFactory.build_pod(set_pod_parser().parse_args(args))
        self.pod.start()


class FlowStore(BaseStore):
    _kind = 'flow'
    _status_model = PartialStoreStatus

    def __init__(self, args):
        super().__init__()
        self.flow = Flow(set_flow_parser().parse_args(args))
        self.flow.start()
