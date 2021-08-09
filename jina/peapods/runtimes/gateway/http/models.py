from collections import defaultdict
from datetime import datetime
from enum import Enum
from types import SimpleNamespace
from typing import Callable, Dict, Any, Optional, List, Union, Tuple

from google.protobuf.descriptor import Descriptor, FieldDescriptor
from google.protobuf.json_format import MessageToDict
from google.protobuf.pyext.cpp_message import GeneratedProtocolMessageType
from pydantic import Field, BaseModel, BaseConfig, create_model, root_validator

from .....proto import jina_pb2
from .....proto.jina_pb2 import (
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
)
from .....types.document import Document

PROTO_TO_PYDANTIC_MODELS = SimpleNamespace()
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


class CustomConfig(BaseConfig):
    """Pydantic config for Camel case and enum handling"""

    use_enum_values = True
    allow_population_by_field_name = True


def _get_oneof_validator(oneof_fields: List, oneof_key: str) -> Callable:
    """
    Pydantic root validator (pre) classmethod generator to confirm only one oneof field is passed

    :param oneof_fields: list of field names for oneof
    :type oneof_fields: List
    :param oneof_key: oneof key
    :type oneof_key: str
    :return: classmethod for validating oneof fields
    """

    def oneof_validator(cls, values):
        if len(set(oneof_fields).intersection(set(values))) > 1:
            raise ValueError(
                f'only one field among {oneof_fields} can be set for key {oneof_key}!'
            )
        return values

    oneof_validator.__qualname__ = 'validate_' + oneof_key
    return root_validator(pre=True, allow_reuse=True)(oneof_validator)


def _get_oneof_setter(oneof_fields: List, oneof_key: str) -> Callable:
    """
    Pydantic root validator (post) classmethod generator to set the oneof key

    :param oneof_fields: list of field names for oneof
    :type oneof_fields: List
    :param oneof_key: oneof key
    :type oneof_key: str
    :return: classmethod for setting oneof fields in Pydantic models
    """

    def oneof_setter(cls, values):
        for oneof_field in oneof_fields:
            if (
                oneof_field in values
                and values[oneof_field] == cls.__fields__[oneof_field].default
            ):
                values.pop(oneof_field)
        return values

    oneof_setter.__qualname__ = 'set_' + oneof_key
    return root_validator(pre=False, allow_reuse=True)(oneof_setter)


def _get_tags_updater() -> Callable:
    """
    Pydantic root validator (pre) classmethod generator to update tags

    :return: classmethod for updating tags in DocumentProto Pydantic model
    """

    def tags_updater(cls, values):
        extra_fields = {k: values[k] for k in set(values).difference(cls.__fields__)}
        if extra_fields:
            if 'tags' not in values:
                values['tags'] = {}
            if isinstance(values['tags'], Dict):
                values['tags'].update(extra_fields)
        return values

    return root_validator(pre=True, allow_reuse=True)(tags_updater)


def protobuf_to_pydantic_model(
    protobuf_model: Union[Descriptor, GeneratedProtocolMessageType]
) -> BaseModel:
    """
    Converts Protobuf messages to Pydantic model for jsonschema creation/validattion

    ..note:: Model gets assigned in the global Namespace :data:PROTO_TO_PYDANTIC_MODELS

    :param protobuf_model: message from jina.proto file
    :type protobuf_model: Union[Descriptor, GeneratedProtocolMessageType]
    :return: Pydantic model
    """

    all_fields = {}
    camel_case_fields = {}  # {"random_string": {"alias": "randomString"}}
    oneof_fields = defaultdict(list)
    oneof_field_validators = {}

    if isinstance(protobuf_model, Descriptor):
        model_name = protobuf_model.name
        protobuf_fields = protobuf_model.fields
    elif isinstance(protobuf_model, GeneratedProtocolMessageType):
        model_name = protobuf_model.DESCRIPTOR.name
        protobuf_fields = protobuf_model.DESCRIPTOR.fields

    if model_name in vars(PROTO_TO_PYDANTIC_MODELS):
        return PROTO_TO_PYDANTIC_MODELS.__getattribute__(model_name)

    for f in protobuf_fields:
        field_name = f.name
        camel_case_fields[field_name] = {'alias': f.camelcase_name}

        field_type = PROTOBUF_TO_PYTHON_TYPE[f.type]
        default_value = f.default_value
        default_factory = None

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
                default_factory = dict
            elif f.message_type.name == 'Timestamp':
                # Proto Field Type: google.protobuf.Timestamp
                field_type = datetime
                default_factory = datetime.now
            else:
                # Proto field type: Proto message defined in jina.proto
                if f.message_type.name == model_name:
                    # Self-referencing models
                    field_type = model_name
                else:
                    # This field_type itself a Pydantic model
                    field_type = protobuf_to_pydantic_model(f.message_type)
                    PROTO_TO_PYDANTIC_MODELS.model_name = field_type

        if f.label == FieldDescriptor.LABEL_REPEATED:
            field_type = List[field_type]

        all_fields[field_name] = (
            field_type,
            Field(default_factory=default_factory)
            if default_factory
            else Field(default=default_value),
        )

        # some fixes on Doc.scores and Doc.evaluations
        if field_name in ('scores', 'evaluations'):
            all_fields[field_name] = (
                Dict[str, PROTO_TO_PYDANTIC_MODELS.NamedScoreProto],
                Field(default={}),
            )

    # Post-processing (Handle oneof fields)
    for oneof_k, oneof_v_list in oneof_fields.items():
        oneof_field_validators[f'oneof_validator_{oneof_k}'] = _get_oneof_validator(
            oneof_fields=oneof_v_list, oneof_key=oneof_k
        )
        oneof_field_validators[f'oneof_setter_{oneof_k}'] = _get_oneof_setter(
            oneof_fields=oneof_v_list, oneof_key=oneof_k
        )

    if model_name == 'DocumentProto':
        oneof_field_validators['tags_validator'] = _get_tags_updater()

    CustomConfig.fields = camel_case_fields
    model = create_model(
        model_name,
        **all_fields,
        __config__=CustomConfig,
        __validators__=oneof_field_validators,
    )
    model.update_forward_refs()
    PROTO_TO_PYDANTIC_MODELS.__setattr__(model_name, model)
    return model


for proto in (
    NamedScoreProto,
    DenseNdArrayProto,
    NdArrayProto,
    SparseNdArrayProto,
    DocumentProto,
    RouteProto,
    EnvelopeProto,
    StatusProto,
    MessageProto,
    RequestProto,
):
    protobuf_to_pydantic_model(proto)


def _to_camel_case(snake_str: str) -> str:
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])


class JinaStatusModel(BaseModel):
    """Pydantic BaseModel for Jina status, used as the response model in REST app."""

    jina: Dict
    envs: Dict
    used_memory: str

    class Config:
        alias_generator = _to_camel_case
        allow_population_by_field_name = True


def _get_example_data():
    _example = jina_pb2.DocumentArrayProto()
    d0 = Document(id='🐲', tags={'guardian': 'Azure Dragon', 'position': 'East'})
    d1 = Document(id='🐦', tags={'guardian': 'Vermilion Bird', 'position': 'South'})
    d2 = Document(id='🐢', tags={'guardian': 'Black Tortoise', 'position': 'North'})
    d3 = Document(id='🐯', tags={'guardian': 'White Tiger', 'position': 'West'})
    d0.chunks.append(d1)
    d0.chunks[0].chunks.append(d2)
    d0.matches.append(d3)
    _example.docs.extend([d0.proto, d1.proto, d2.proto, d3.proto])
    return MessageToDict(
        _example,
        including_default_value_fields=True,
    )['docs']


class JinaRequestModel(BaseModel):
    """
    Jina HTTP request model.
    """

    data: Optional[
        Union[
            List[PROTO_TO_PYDANTIC_MODELS.DocumentProto],
            List[Dict[str, Any]],
            List[str],
            List[bytes],
        ]
    ] = Field(
        None,
        example=_get_example_data(),
        description='Data to send, a list of dict/string/bytes that can be converted into a list of `Document` objects',
    )
    target_peapod: Optional[str] = Field(
        None,
        example='pod0/*',
        description='A regex string represent the certain peas/pods request targeted.',
    )
    parameters: Optional[Dict] = Field(
        None,
        example={'top_k': 3, 'model': 'bert'},
        description='A dictionary of parameters to be sent to the executor.',
    )

    class Config:
        alias_generator = _to_camel_case
        allow_population_by_field_name = True


class JinaResponseModel(BaseModel):
    """
    Jina HTTP Response model. Only `request_id` and `data` are preserved.
    """

    class DataRequestModel(BaseModel):
        docs: Optional[List[Dict[str, Any]]] = None
        groundtruths: Optional[List[Dict[str, Any]]] = None

    request_id: str = Field(
        ...,
        example='b5110ed9-1954-4a3d-9180-0795a1e0d7d8',
        description='The ID given by Jina service',
    )
    data: Optional[DataRequestModel] = Field(None, description='Returned Documents')

    class Config:
        alias_generator = _to_camel_case
        allow_population_by_field_name = True


class JinaEndpointRequestModel(JinaRequestModel):
    """
    Jina HTTP request model that allows customized endpoint.
    """

    exec_endpoint: str = Field(
        ...,
        example='/foo',
        description='The endpoint string, by convention starts with `/`. '
        'All executors bind with `@requests(on="/foo")` will receive this request.',
    )
