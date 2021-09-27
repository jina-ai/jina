from typing import Dict

from pydantic import BaseModel, Field

from .base import StoreItem, StoreStatus
from .id import DaemonID


class ContainerArguments(BaseModel):
    """Pydantic model for ContainerArguments"""

    object: Dict
    entrypoint: str


class ContainerMetadata(BaseModel):
    """Pydantic model for ContainerMetadata"""

    container_id: str
    container_name: str
    image_id: str
    network: str
    ports: Dict
    uri: str


class ContainerItem(StoreItem):
    """Pydantic model for ContainerItem"""

    metadata: ContainerMetadata
    arguments: ContainerArguments
    workspace_id: DaemonID


class ContainerStoreStatus(StoreStatus):
    """Pydantic model for ContainerStoreStatus"""

    items: Dict[DaemonID, ContainerItem] = Field(default_factory=dict)
