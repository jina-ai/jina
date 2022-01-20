import pytest

from jina.serve.runtimes.gateway.http.models import (
    PROTO_TO_PYDANTIC_MODELS,
    JinaRequestModel,
)


def test_schema_invocation():
    for k, v in vars(PROTO_TO_PYDANTIC_MODELS).items():
        v.schema()
        v.schema_json()


def test_enum_definitions():
    """This tests: all enums are defined properly as different levels"""
    status_code_enum_definition = PROTO_TO_PYDANTIC_MODELS.StatusProto().schema()[
        'definitions'
    ]['StatusCode']
    assert status_code_enum_definition['enum'] == [0, 1, 2, 3, 4, 5, 6]


def test_timestamp():
    """This tests: google.protobuf.Timestamp are represented as date-time"""
    assert (
        PROTO_TO_PYDANTIC_MODELS.RouteProto().schema(by_alias=False)['properties'][
            'start_time'
        ]['type']
        == 'string'
    )
    assert (
        PROTO_TO_PYDANTIC_MODELS.RouteProto().schema(by_alias=False)['properties'][
            'start_time'
        ]['format']
        == 'date-time'
    )


@pytest.mark.parametrize('top_k', [5, 10])
def test_model_with_top_k(top_k):
    m = JinaRequestModel(data=['abc'], parameters={'top_k': top_k})
    assert m.parameters['top_k'] == top_k

    m = JinaRequestModel(parameters={'top_k': top_k})
    assert m.parameters['top_k'] == top_k
