from typing import Dict, List
from pydantic import BaseModel

from .id import DaemonID
from .base import StoreItem, StoreStatus


class WorkspaceArguments(BaseModel):
    files: List[str]
    jinad: Dict[str, str]
    requirements: List


class WorkspaceMetadata(BaseModel):
    image_id: str
    image_name: str
    network: str
    ports: Dict[str, int]
    workdir: str


class WorkspaceItem(StoreItem):
    metadata: WorkspaceMetadata
    arguments: WorkspaceArguments


class WorkspaceStoreStatus(StoreStatus):
    items: Dict[DaemonID, WorkspaceItem]
