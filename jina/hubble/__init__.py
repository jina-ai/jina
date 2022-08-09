from dataclasses import dataclass
from typing import Optional


@dataclass
class HubExecutor:
    """Basic Executor Data Class from Hubble"""

    uuid: str = None
    name: Optional[str] = None
    commit_id: Optional[str] = None
    tag: Optional[str] = None
    visibility: Optional[bool] = None
    image_name: Optional[str] = None
    archive_url: Optional[str] = None
    md5sum: Optional[str] = None
    build_env: Optional[list] = None
