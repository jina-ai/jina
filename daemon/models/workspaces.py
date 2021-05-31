from typing import Dict, List, Optional
from pydantic import BaseModel

from .id import DaemonID
from .enums import WorkspaceState
from .base import StoreItem, StoreStatus


class WorkspaceArguments(BaseModel):
    files: List[str]
    jinad: Dict[str, str]
    requirements: str


class WorkspaceMetadata(BaseModel):
    image_id: str
    image_name: str
    network: str
    ports: Dict[str, int]
    workdir: str


class WorkspaceItem(StoreItem):
    state: WorkspaceState
    metadata: Optional[WorkspaceMetadata]
    arguments: Optional[WorkspaceArguments]


class WorkspaceStoreStatus(StoreStatus):
    items: Dict[DaemonID, WorkspaceItem]
