from typing import Dict

from pydantic.main import BaseModel


class JinaStatus(BaseModel):
    jina: Dict
    envs: Dict
    used_memory: str
