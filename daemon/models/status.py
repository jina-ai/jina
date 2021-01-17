import uuid
from datetime import datetime
from typing import Dict

from pydantic import BaseModel


class StorePeaPodStatus(BaseModel):
    uptime: datetime
    arguments: Dict


class StoreStatus(BaseModel):
    size: int
    uptime: datetime
    last_update: datetime
    num_add: int
    num_del: int
    items: Dict[uuid.UUID, StorePeaPodStatus]


class DaemonStatus(BaseModel):
    jina: Dict
    peas: StoreStatus
    pods: StoreStatus
    flows: StoreStatus
    used_memory: str
