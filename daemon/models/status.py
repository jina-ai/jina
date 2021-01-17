import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class StoreStatus(BaseModel):
    size: int
    uptime: datetime
    last_update: datetime
    num_add: int
    num_del: int
    items: Optional[List['uuid.UUID']]
