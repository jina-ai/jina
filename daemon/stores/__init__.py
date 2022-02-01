from typing import Optional, TYPE_CHECKING, Type, Union

from daemon.stores.base import BaseStore
from daemon.stores.flows import FlowStore
from daemon.stores.pods import PodStore
from daemon.stores.deployments import DeploymentStore
from daemon.stores.workspaces import WorkspaceStore
from daemon import jinad_args
from daemon.models import DaemonID
from daemon.models.enums import IDLiterals

if TYPE_CHECKING:
    from daemon.stores.partial import (
        PartialPodStore,
        PartialDeploymentStore,
        PartialFlowStore,
    )


def _get_store(cls: Type[BaseStore]) -> BaseStore:
    """Get store object from cls

    :param cls: store class
    :return: store object
    """

    if jinad_args.no_store:
        return cls()
    else:
        try:
            return cls.load()
        except Exception:
            return cls()


def _get_partial_store() -> Optional[
    Union['PartialPodStore', 'PartialDeploymentStore', 'PartialFlowStore']
]:
    """Get partial store object

    :return: partial store object
    """
    from daemon.models.enums import PartialDaemonModes
    from daemon.stores.partial import (
        PartialPodStore,
        PartialDeploymentStore,
        PartialFlowStore,
    )

    if jinad_args.mode == PartialDaemonModes.POD:
        return PartialPodStore()
    elif jinad_args.mode == PartialDaemonModes.DEPLOYMENT:
        return PartialDeploymentStore()
    elif jinad_args.mode == PartialDaemonModes.FLOW:
        return PartialFlowStore()
    else:
        return None


def get_store_from_id(entity_id: DaemonID) -> Optional[BaseStore]:
    """Get store from id

    :param entity_id: DaemonID
    :return: store object
    """
    if entity_id.jtype == IDLiterals.JDEPLOYMENT:
        return deployment_store
    elif entity_id.jtype == IDLiterals.JPOD:
        return pod_store
    elif entity_id.jtype == IDLiterals.JFLOW:
        return flow_store
    elif entity_id.jtype == IDLiterals.JWORKSPACE:
        return workspace_store
    else:
        return None


pod_store: PodStore = _get_store(PodStore)
deployment_store: DeploymentStore = _get_store(DeploymentStore)
flow_store: FlowStore = _get_store(FlowStore)
workspace_store: WorkspaceStore = _get_store(WorkspaceStore)
partial_store = _get_partial_store()
