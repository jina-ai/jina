from typing import Dict, Any, Optional, List, Union

from enum import Enum
from datetime import datetime
from collections import defaultdict

from pydantic import Field, BaseModel, BaseConfig, create_model
from google.protobuf.descriptor import Descriptor, FieldDescriptor
from google.protobuf.pyext.cpp_message import GeneratedProtocolMessageType

from jina.enums import DataInputType
from jina.types.document import Document
from jina.parsers import set_client_cli_parser
from jina.proto.jina_pb2 import (
    DenseNdArrayProto,
    NdArrayProto,
    SparseNdArrayProto,
    NamedScoreProto,
    DocumentProto,
    RouteProto,
    EnvelopeProto,
    StatusProto,
    MessageProto,
    RequestProto,
    QueryLangProto,
)

DEFAULT_REQUEST_SIZE = set_client_cli_parser().parse_args([]).request_size
PROTO_TO_PYDANTIC_MODELS = {}
PROTOBUF_TO_PYTHON_TYPE = {
    FieldDescriptor.TYPE_INT32: int,
    FieldDescriptor.TYPE_INT64: int,
    FieldDescriptor.TYPE_UINT32: int,
    FieldDescriptor.TYPE_UINT64: int,
    FieldDescriptor.TYPE_SINT32: int,
    FieldDescriptor.TYPE_SINT64: int,
    FieldDescriptor.TYPE_BOOL: bool,
    FieldDescriptor.TYPE_FLOAT: float,
    FieldDescriptor.TYPE_DOUBLE: float,
    FieldDescriptor.TYPE_FIXED32: float,
    FieldDescriptor.TYPE_FIXED64: float,
    FieldDescriptor.TYPE_SFIXED32: float,
    FieldDescriptor.TYPE_SFIXED64: float,
    FieldDescriptor.TYPE_BYTES: bytes,
    FieldDescriptor.TYPE_STRING: str,
    FieldDescriptor.TYPE_ENUM: Enum,
    FieldDescriptor.TYPE_MESSAGE: None,
}


class CamelCaseConfig(BaseConfig):
    """Pydantic config for Camel case handling"""

    allow_population_by_field_name = True


def protobuf_to_pydantic_model(
    protobuf_model: Union[Descriptor, GeneratedProtocolMessageType]
) -> BaseModel:
    """
    Converts Protobuf messages to Pydantic model for jsonschema creation/validattion

    ..note:: Model gets assigned in the global dict :data:PROTO_TO_PYDANTIC_MODELS

    :param protobuf_model: *Proto message from proto file
    :type protobuf_model: Union[Descriptor, GeneratedProtocolMessageType]
    :return: Pydantic model
    :rtype: BaseModel
    """

    all_fields = {}
    camel_case_fields = {}  # {"random_string": {"alias": "randomString"}}
    oneof_fields = defaultdict(list)

    if isinstance(protobuf_model, Descriptor):
        model_name = protobuf_model.name
        protobuf_fields = protobuf_model.fields
    elif isinstance(protobuf_model, GeneratedProtocolMessageType):
        model_name = protobuf_model.DESCRIPTOR.name
        protobuf_fields = protobuf_model.DESCRIPTOR.fields

    if model_name in PROTO_TO_PYDANTIC_MODELS:
        return PROTO_TO_PYDANTIC_MODELS[model_name]

    for f in protobuf_fields:
        field_name = f.name
        camel_case_fields[field_name] = {'alias': f.camelcase_name}

        field_type = PROTOBUF_TO_PYTHON_TYPE[f.type]
        default_value = f.default_value

        if f.containing_oneof:
            # Proto Field type: oneof
            # NOTE: oneof fields are handled as a post-processing step
            oneof_fields[f.containing_oneof.name].append(field_name)

        if field_type is Enum:
            # Proto Field Type: enum
            enum_dict = {}
            for enum_field in f.enum_type.values:
                enum_dict[enum_field.name] = enum_field.number
            field_type = Enum(f.enum_type.name, enum_dict)

        if f.message_type:

            if f.message_type.name == 'Struct':
                # Proto Field Type: google.protobuf.Struct
                field_type = Dict
                default_value = {}

            elif f.message_type.name == 'Timestamp':
                # Proto Field Type: google.protobuf.Timestamp
                field_type = datetime
                default_value = datetime.now()

            else:
                # Proto field type: Another Proto message in jina
                # (every proto message in Jina ends with 'Proto')

                if f.message_type.name == model_name:
                    # Self-referencing models
                    field_type = model_name
                else:
                    field_type = protobuf_to_pydantic_model(f.message_type)
                    PROTO_TO_PYDANTIC_MODELS[model_name] = field_type

        if f.label == FieldDescriptor.LABEL_REPEATED:
            field_type = List[field_type]

        all_fields[field_name] = (field_type, Field(default=default_value))

    # Post-processing (Handle oneof fields)
    for oneof_k, oneof_v_list in oneof_fields.items():
        union_types = []
        for oneof_v in oneof_v_list:
            ff = all_fields[oneof_v]
            union_types.append(ff[0])
        all_fields[oneof_k] = (Union[tuple(union_types)], Field(None))
        # TODO: fix camel case for oneof_k
        camel_case_fields[oneof_k] = {'alias': oneof_k}

    CamelCaseConfig.fields = camel_case_fields
    model = create_model(model_name, **all_fields, __config__=CamelCaseConfig)
    model.update_forward_refs()
    PROTO_TO_PYDANTIC_MODELS[model_name] = model
    return model


for proto in (
    DenseNdArrayProto,
    NdArrayProto,
    SparseNdArrayProto,
    NamedScoreProto,
    DocumentProto,
    RouteProto,
    EnvelopeProto,
    StatusProto,
    MessageProto,
    RequestProto,
    QueryLangProto,
):
    protobuf_to_pydantic_model(proto)


class JinaStatusModel(BaseModel):
    """Pydantic BaseModel for Jina status, used as the response model in REST app."""

    jina: Dict
    envs: Dict
    used_memory: str


class JinaRequestModel(BaseModel):
    """
    Jina request model.

    The base model for Jina REST request.
    """

    # To avoid an error while loading the request model schema on swagger, we've added an example.
    data: Union[
        List[PROTO_TO_PYDANTIC_MODELS['DocumentProto']],
        List[Dict[str, Any]],
        List[str],
        List[bytes],
    ] = Field(..., example=[Document().dict()])
    request_size: Optional[int] = DEFAULT_REQUEST_SIZE
    mime_type: Optional[str] = ''
    queryset: Optional[List[PROTO_TO_PYDANTIC_MODELS['QueryLangProto']]] = None
    data_type: DataInputType = DataInputType.AUTO


class JinaIndexRequestModel(JinaRequestModel):
    """Index request model."""

    pass


class JinaSearchRequestModel(JinaRequestModel):
    """Search request model."""

    pass


class JinaUpdateRequestModel(JinaRequestModel):
    """Update request model."""

    pass


class JinaDeleteRequestModel(JinaRequestModel):
    """Delete request model."""

    data: List[str]


class JinaControlRequestModel(JinaRequestModel):
    """Control request model."""

    pass


class JinaTrainRequestModel(JinaRequestModel):
    """Train request model."""

    pass
