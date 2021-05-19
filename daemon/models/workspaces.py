from typing import Dict, List
from pydantic import BaseModel

from .id import DaemonID
from .base import StoreItem, StoreStatus


class WorkspaceArguments(BaseModel):
    files: List[str]
    jinad: str
    requirements: List


class WorkspaceMetadata(BaseModel):
    image_id: str
    image_name: str
    network: str
    workdir: str


class WorkspaceItem(StoreItem):
    metadata: WorkspaceMetadata
    arguments: WorkspaceArguments


class WorkspaceStoreStatus(StoreStatus):
    items: Dict[DaemonID, WorkspaceItem]
