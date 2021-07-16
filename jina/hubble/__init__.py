from dataclasses import dataclass
from typing import Optional


@dataclass
class HubExecutor:
    """Basic Executor Data Class from Hubble"""

    uuid: str = None
    alias: Optional[str] = None
    sn: Optional[int] = None
    tag: Optional[str] = None
    visibility: Optional[bool] = None
    image_name: Optional[str] = None
    archive_url: Optional[str] = None
    md5sum: Optional[str] = None
