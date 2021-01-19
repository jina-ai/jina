import uuid
from datetime import datetime
from typing import Dict, Union, List

from pydantic import BaseModel


class StoreItemStatus(BaseModel):
    time_created: datetime
    arguments: Union[Dict, List]
    workspace_id: uuid.UUID
    workdir: str


class FlowItemStatus(StoreItemStatus):
    yaml_source: str


class StoreStatus(BaseModel):
    size: int
    time_created: datetime
    time_updated: datetime
    num_add: int
    num_del: int
    items: Dict[uuid.UUID, StoreItemStatus]


class FlowStoreStatus(StoreStatus):
    items: Dict[uuid.UUID, FlowItemStatus]


class DaemonStatus(BaseModel):
    jina: Dict
    envs: Dict
    peas: StoreStatus
    pods: StoreStatus
    flows: FlowStoreStatus
    workspaces: StoreStatus
    used_memory: str
