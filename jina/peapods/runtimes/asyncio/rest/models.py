from typing import Dict, Any, Optional, List

from pydantic.main import BaseModel

from jina.enums import RequestType, DataInputType


class JinaStatusModel(BaseModel):
    jina: Dict
    envs: Dict
    used_memory: str


class JinaRequestModel(BaseModel):
    data: List[Dict[str, Any]]
    request_size: Optional[int] = 0
    mode: RequestType
    mime_type: Optional[str] = None
    queryset: List[Dict[str, Any]]
    data_type: DataInputType = DataInputType.AUTO


class JinaIndexRequestModel(JinaRequestModel):
    mode: RequestType = RequestType.INDEX


class JinaSearchRequestModel(JinaRequestModel):
    mode: RequestType = RequestType.SEARCH


class JinaUpdateRequestModel(JinaRequestModel):
    mode: RequestType = RequestType.UPDATE


class JinaDeleteRequestModel(JinaRequestModel):
    mode: RequestType = RequestType.DELETE


class JinaControlRequestModel(JinaRequestModel):
    mode: RequestType = RequestType.CONTROL


class JinaTrainRequestModel(JinaRequestModel):
    mode: RequestType = RequestType.TRAIN
