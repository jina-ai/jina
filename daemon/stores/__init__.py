from typing import Optional, TYPE_CHECKING

from .base import BaseStore
from .flows import FlowStore
from .peas import PeaStore
from .pods import PodStore
from .workspaces import WorkspaceStore
from .. import jinad_args
from ..models import DaemonID
from ..models.enums import IDLiterals

if TYPE_CHECKING:
    from .partial import PartialStore


def _get_store(kind: str):
    """Get store object

    :param kind:  store kind
    :return: store object
    """
    if kind == 'pea':
        cls = PeaStore
    elif kind == 'pod':
        cls = PodStore
    elif kind == 'flow':
        cls = FlowStore
    elif kind == 'workspace':
        cls = WorkspaceStore

    if jinad_args.no_store:
        return cls()
    else:
        try:
            return cls.load()
        except Exception:
            return cls()


def _get_partial_store() -> Optional['PartialStore']:
    """Get partial store object

    :return: partial store object
    """
    from ..models.enums import PartialDaemonModes
    from .partial import PartialPeaStore, PartialPodStore, PartialFlowStore

    if jinad_args.mode == PartialDaemonModes.PEA:
        return PartialPeaStore()
    elif jinad_args.mode == PartialDaemonModes.POD:
        return PartialPodStore()
    elif jinad_args.mode == PartialDaemonModes.FLOW:
        return PartialFlowStore()
    else:
        return None


def get_store_from_id(entity_id: DaemonID) -> BaseStore:
    """Get store from id

    :param entity_id: DaemonID
    :return: store object
    """
    if entity_id.jtype == IDLiterals.JPOD:
        return pod_store
    elif entity_id.jtype == IDLiterals.JPEA:
        return pea_store
    elif entity_id.jtype == IDLiterals.JFLOW:
        return flow_store
    elif entity_id.jtype == IDLiterals.JWORKSPACE:
        return workspace_store
    else:
        return None


pea_store: PeaStore = _get_store('pea')
pod_store: PodStore = _get_store('pod')
flow_store: FlowStore = _get_store('flow')
workspace_store: WorkspaceStore = _get_store('workspace')
partial_store = _get_partial_store()
