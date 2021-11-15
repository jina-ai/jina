from enum import Enum
from typing import Dict

from pydantic import BaseModel

from jina.enums import GatewayProtocolType
from .containers import ContainerItem, ContainerStoreStatus
from .custom import build_pydantic_model
from .id import DaemonID
from .workspaces import WorkspaceItem, WorkspaceStoreStatus

FlowModel = build_pydantic_model(model_name='FlowModel', module='flow')
PodModel = build_pydantic_model(model_name='PodModel', module='pod')
PeaModel = build_pydantic_model(model_name='PeaModel', module='pea')


GATEWAY_RUNTIME_DICT = {
    GatewayProtocolType.GRPC: 'GRPCRuntime',
    GatewayProtocolType.WEBSOCKET: 'WebSocketRuntime',
    GatewayProtocolType.HTTP: 'HTTPRuntime',
}


class DaemonStatus(BaseModel):
    """Pydantic model for DaemonStatus"""

    jina: Dict
    envs: Dict
    workspaces: WorkspaceStoreStatus
    peas: ContainerStoreStatus
    pods: ContainerStoreStatus
    flows: ContainerStoreStatus
    used_memory: str
