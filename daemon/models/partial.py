from typing import Dict

from pydantic import Field

from .base import StoreItem, StoreStatus


class PartialStoreItem(StoreItem):
    """Pydantic model for PartialStoreItem"""

    arguments: Dict = Field(default_factory=dict)


class PartialFlowItem(PartialStoreItem):
    """Pydantic model for PartialFlowItem"""

    yaml_source: str = ''


class PartialStoreStatus(StoreStatus):
    """Pydantic model for PartialStoreStatus"""

    items: StoreItem = StoreItem()

    def __len__(self):
        return 1
