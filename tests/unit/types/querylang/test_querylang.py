import pytest
from google.protobuf.json_format import MessageToDict, MessageToJson

from jina.types.querylang import QueryLang


def test_ql_constructors_from_driver_info():
    q = QueryLang(
        {'name': 'SliceQL', 'parameters': {'start': 3, 'end': 5}, 'priority': 999}
    )
    qb = q.proto
    assert q.name == 'SliceQL'
    assert q.parameters['start'] == 3
    assert q.parameters['end'] == 5
    assert q.priority == 999

    assert qb.name == 'SliceQL'
    assert qb.parameters['start'] == 3
    assert qb.parameters['end'] == 5
    assert qb.priority == 999


@pytest.mark.parametrize(
    'source',
    [
        lambda x: x.SerializeToString(),
        lambda x: MessageToDict(x),
        lambda x: MessageToJson(x),
        lambda x: x,
    ],
)
def test_ql_constructors_from_proto(source):
    q = QueryLang(
        {'name': 'SliceQL', 'parameters': {'start': 3, 'end': 5}, 'priority': 999}
    ).proto

    qlr = QueryLang(source(q))
    assert qlr.name == 'SliceQL'
    assert qlr.parameters['start'] == 3
    assert qlr.parameters['end'] == 5
    assert qlr.priority == 999


def test_ql_priority():
    qs = QueryLang(
        {'name': 'SliceQL', 'parameters': {'start': 1, 'end': 4}, 'priority': 1}
    )
    assert qs.priority == 1
    qs._pb_body.priority = -1
    assert qs._pb_body.priority == -1
    assert qs.priority == -1

    qs.priority = -2
    assert qs._pb_body.priority == -2
    assert qs.priority == -2

    qs2 = QueryLang({'name': 'SliceQL', 'parameters': {'start': 1, 'end': 4}})
    assert qs2.priority == 0
