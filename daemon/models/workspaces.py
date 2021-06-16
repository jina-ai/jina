from ipaddress import IPv4Address
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

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
    workdir: str
    container_id: Optional[str]
    managed_objects: Set[DaemonID] = Field(default_factory=set)


class WorkspaceItem(StoreItem):
    state: WorkspaceState
    metadata: Optional[WorkspaceMetadata]
    arguments: Optional[WorkspaceArguments]


class WorkspaceStoreStatus(StoreStatus):
    ip_range_start: IPv4Address = IPv4Address('10.0.0.0')
    subnet_size: int = 22
    ip_range_current_offset: int = 0
    items: Dict[DaemonID, WorkspaceItem] = Field(default_factory=dict)
