import pytest
from google.protobuf.json_format import MessageToDict, MessageToJson

from jina.drivers.querylang.slice import SliceQL
from jina.types.querylang import QueryLang


def test_ql_constructors_from_driver():
    ql = SliceQL(start=3, end=5, priority=999)
    q = QueryLang(ql)
    qb = q.as_pb_object
    assert q.name == 'SliceQL'
    assert q.parameters['start'] == 3
    assert q.parameters['end'] == 5
    assert q.priority == 999

    assert qb.name == 'SliceQL'
    assert qb.parameters['start'] == 3
    assert qb.parameters['end'] == 5
    assert qb.priority == 999

    assert isinstance(q.as_driver_object, SliceQL)
    assert ql.start == q.as_driver_object.start
    assert ql.end == q.as_driver_object.end
    assert ql._priority == q.as_driver_object._priority


@pytest.mark.parametrize('source', [lambda x: x.SerializeToString(),
                                    lambda x: MessageToDict(x),
                                    lambda x: MessageToJson(x),
                                    lambda x: x])
def test_ql_constructors_from_proto(source):
    ql = SliceQL(start=3, end=5, priority=999)
    q = QueryLang(ql).as_pb_object

    qlr = QueryLang(source(q))
    assert qlr.name == 'SliceQL'
    assert qlr.parameters['start'] == 3
    assert qlr.parameters['end'] == 5
    assert qlr.priority == 999


def test_ql_priority():
    qs = QueryLang(SliceQL(start=1, end=4, priority=1))
    assert qs.priority == 1
    qs._querylang.priority = -1
    assert qs._querylang.priority == -1
    assert qs.priority == -1

    qs.priority = -2
    assert qs._querylang.priority == -2
    assert qs.priority == -2
