from typing import Dict
from datetime import datetime
from pydantic import BaseModel

from .id import DaemonID


class StoreItem(BaseModel):
    time_created: datetime


class StoreStatus(BaseModel):
    size: int
    time_created: datetime
    time_updated: datetime
    num_add: int
    num_del: int
    items: Dict[DaemonID, StoreItem]
