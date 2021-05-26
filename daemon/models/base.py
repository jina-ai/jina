from typing import Dict
from datetime import datetime
from pydantic import BaseModel, root_validator, Field

from .id import DaemonID


class StoreItem(BaseModel):
    time_created: datetime = Field(default_factory=datetime.now)


class StoreStatus(BaseModel):
    size: int = 0
    time_created: datetime = Field(default_factory=datetime.now)
    time_updated: datetime = Field(default_factory=datetime.now)
    num_add: int = 0
    num_del: int = 0
    items: Dict[DaemonID, StoreItem] = Field(default_factory=dict)

    @root_validator(pre=False)
    def set_size(cls, values):
        if 'items' in values:
            values['size'] = len(values['items'])
        elif 'size' not in values:
            values['size'] = 0
        return values
