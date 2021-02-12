from typing import Dict, Any, Optional, List, Union

from pydantic import Field
from pydantic.main import BaseModel, create_model

from jina.enums import DataInputType
from jina.proto.jina_pb2 import DocumentProto, QueryLangProto


class JinaStatusModel(BaseModel):
    jina: Dict
    envs: Dict
    used_memory: str


def build_model_from_pb(name, pb_model):
    from google.protobuf.json_format import MessageToDict

    dp = MessageToDict(pb_model(), including_default_value_fields=True)

    all_fields = {k: (name if k in ('chunks', 'matches') else type(v), Field(default=v)) for k, v in dp.items()}
    if pb_model == QueryLangProto:
        all_fields['parameters'] = (Dict, Field(default={}))

    return create_model(name, **all_fields)


JinaDocumentModel = build_model_from_pb('Document', DocumentProto)
JinaDocumentModel.update_forward_refs()
JinaQueryLangModel = build_model_from_pb('QueryLang', QueryLangProto)


class JinaRequestModel(BaseModel):
    data: Union[List[JinaDocumentModel], List[Dict[str, Any]], List[str], List[bytes]]
    request_size: Optional[int] = 0
    mime_type: Optional[str] = None
    queryset: Optional[List[JinaQueryLangModel]] = None
    data_type: DataInputType = DataInputType.AUTO


class JinaIndexRequestModel(JinaRequestModel):
    pass


class JinaSearchRequestModel(JinaRequestModel):
    pass


class JinaUpdateRequestModel(JinaRequestModel):
    pass


class JinaDeleteRequestModel(JinaRequestModel):
    data: List[str]


class JinaControlRequestModel(JinaRequestModel):
    pass


class JinaTrainRequestModel(JinaRequestModel):
    pass
