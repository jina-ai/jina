from typing import Dict
from pydantic import BaseModel, Field

from .id import DaemonID
from .base import StoreItem, StoreStatus


class ContainerArguments(BaseModel):
    command: str


class ContainerMetadata(BaseModel):
    container_id: str
    container_name: str
    image_id: str
    network: str
    ports: Dict
    host: str


class ContainerItem(StoreItem):
    metadata: ContainerMetadata
    arguments: ContainerArguments
    workspace_id: DaemonID


class ContainerStoreStatus(StoreStatus):
    items: Dict[DaemonID, ContainerItem] = Field(default_factory=dict)
