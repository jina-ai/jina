from datetime import datetime
from typing import Dict

from pydantic import BaseModel, Field

from .id import DaemonID


class StoreItem(BaseModel):
    """Pydantic model for StoreItem"""

    time_created: datetime = Field(default_factory=datetime.now)


class StoreStatus(BaseModel):
    """Pydantic model for StoreStatus"""

    time_created: datetime = Field(default_factory=datetime.now)
    time_updated: datetime = Field(default_factory=datetime.now)
    num_add: int = 0
    num_del: int = 0
    items: Dict[DaemonID, StoreItem] = Field(default_factory=dict)

    def __len__(self):
        return len(self.items)
