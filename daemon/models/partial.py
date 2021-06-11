from typing import Dict
from pydantic import Field

from .base import StoreItem, StoreStatus


class PartialStoreItem(StoreItem):
    arguments: Dict = Field(default_factory=dict)


class PartialFlowItem(PartialStoreItem):
    yaml_source: str = ''


class PartialStoreStatus(StoreStatus):
    items: StoreItem = StoreItem()

    def __len__(self):
        return 1
