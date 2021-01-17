import uuid
from datetime import datetime
from typing import Dict

from pydantic import BaseModel


class StoreItemStatus(BaseModel):
    uptime: datetime
    arguments: Dict


class FlowItemStatus(StoreItemStatus):
    yaml_source: str


class StoreStatus(BaseModel):
    size: int
    uptime: datetime
    last_update: datetime
    num_add: int
    num_del: int
    items: Dict[uuid.UUID, StoreItemStatus]


class FlowStoreStatus(StoreStatus):
    items: Dict[uuid.UUID, FlowItemStatus]


class DaemonStatus(BaseModel):
    jina: Dict
    peas: StoreStatus
    pods: StoreStatus
    flows: StoreStatus
    used_memory: str
