from typing import Callable, Dict, Any, Optional, List, Union

from pydantic import Field, BaseModel, create_model

from jina.enums import DataInputType
from jina.types.document import Document
from jina.parsers import set_client_cli_parser
from jina.proto.jina_pb2 import DocumentProto, QueryLangProto


class JinaStatusModel(BaseModel):
    jina: Dict
    envs: Dict
    used_memory: str


def build_model_from_pb(name: str, pb_model: Callable):
    from google.protobuf.json_format import MessageToDict

    dp = MessageToDict(pb_model(), including_default_value_fields=True)

    all_fields = {k: (name if k in ('chunks', 'matches') else type(v), Field(default=v)) for k, v in dp.items()}
    if pb_model == QueryLangProto:
        all_fields['parameters'] = (Dict, Field(default={}))

    return create_model(name, **all_fields)


JinaDocumentModel = build_model_from_pb('Document', DocumentProto)
JinaDocumentModel.update_forward_refs()
JinaQueryLangModel = build_model_from_pb('QueryLang', QueryLangProto)
default_request_size = set_client_cli_parser().parse_args([]).request_size


class JinaRequestModel(BaseModel):
    # To avoid an error while loading the request model schema on swagger, we've added an example.
    data: Union[List[JinaDocumentModel], List[Dict[str, Any]], List[str], List[bytes]] = \
        Field(..., example=[Document().dict()])
    request_size: Optional[int] = default_request_size
    mime_type: Optional[str] = ''
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
