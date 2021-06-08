from typing import Optional, TYPE_CHECKING

from .. import jinad_args
from .peas import PeaStore
from .pods import PodStore
from .flows import FlowStore
from .workspaces import WorkspaceStore

if TYPE_CHECKING:
    from .partial import PartialStore


def _get_store(kind: str):
    if kind == 'pea':
        cls = PeaStore
    elif kind == 'pod':
        cls = PodStore
    elif kind == 'flow':
        cls = FlowStore
    elif kind == 'workspace':
        cls = WorkspaceStore

    try:
        return cls.load()
    except Exception:
        return cls()


def _get_partial_store() -> Optional['PartialStore']:
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


pea_store: PeaStore = _get_store('pea')
pod_store: PodStore = _get_store('pod')
flow_store: FlowStore = _get_store('flow')
workspace_store: WorkspaceStore = _get_store('workspace')
partial_store = _get_partial_store()
