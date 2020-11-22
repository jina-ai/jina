import sys
from typing import Sequence

import pytest

from jina import Request, QueryLang, Document
from jina.clients.python.request import _generate
from jina.drivers.querylang.slice import SliceQL
from jina.proto import jina_pb2
from jina.proto.jina_pb2 import EnvelopeProto
from jina.types.message import Message
from jina.types.request import _trigger_fields
from tests import random_docs


@pytest.mark.parametrize('field', _trigger_fields.difference({'command', 'args', 'flush'}))
def test_lazy_access(field):
    reqs = (Request(r.SerializeToString(), EnvelopeProto()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used

        # access r.train
        print(getattr(r, field))

        # now it is read
        assert r.is_used


def test_multiple_access():
    reqs = [Request(r.SerializeToString(), EnvelopeProto()) for r in _generate(random_docs(10))]
    for r in reqs:
        assert not r.is_used
        assert r
        assert not r.is_used

    for r in reqs:
        assert not r.is_used
        assert r.index
        assert r.is_used


def test_lazy_nest_access():
    reqs = (Request(r.SerializeToString(), EnvelopeProto()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.docs[0].id = '1' * 16
        # now it is read
        assert r.is_used
        assert r.index.docs[0].id == '1' * 16


def test_lazy_change_message_type():
    reqs = (Request(r.SerializeToString(), EnvelopeProto()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.control.command = jina_pb2.RequestProto.ControlRequestProto.IDLE
        # now it is read
        assert r.is_used
        assert len(r.index.docs) == 0


def test_lazy_append_access():
    reqs = (Request(r.SerializeToString(), EnvelopeProto()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.docs.append(Document())
        # now it is read
        assert r.is_used


def test_lazy_clear_access():
    reqs = (Request(r.SerializeToString(), EnvelopeProto()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.ClearField('index')
        # now it is read
        assert r.is_used


def test_lazy_nested_clear_access():
    reqs = (Request(r.SerializeToString(), EnvelopeProto()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.index.ClearField('docs')
        # now it is read
        assert r.is_used


def test_lazy_msg_access():
    reqs = [Message(None, r.SerializeToString(), 'test', '123',
                    request_id='123', request_type='IndexRequest') for r in _generate(random_docs(10))]
    for r in reqs:
        assert not r.request.is_used
        assert r.envelope
        assert len(r.dump()) == 3
        assert not r.request.is_used

    for r in reqs:
        assert not r.request.is_used
        assert r.request
        assert len(r.dump()) == 3
        assert not r.request.is_used

    for r in reqs:
        assert not r.request.is_used
        assert r.request.index.docs
        assert len(r.dump()) == 3
        assert r.request.is_used


def test_message_size():
    reqs = [Message(None, r, 'test', '123') for r in _generate(random_docs(10))]
    for r in reqs:
        assert r.size == 0
        assert sys.getsizeof(r.envelope.SerializeToString())
        assert sys.getsizeof(r.request.SerializeToString())
        assert len(r.dump()) == 3
        assert r.size > sys.getsizeof(r.envelope.SerializeToString()) \
               + sys.getsizeof(r.request.SerializeToString())


def test_lazy_request_fields():
    reqs = (Request(r.SerializeToString(), EnvelopeProto()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert list(r.DESCRIPTOR.fields_by_name.keys())


def test_request_extend_queryset():
    q1 = SliceQL(start=3, end=4)
    q2 = QueryLang(SliceQL(start=3, end=4, priority=1))
    q3 = jina_pb2.QueryLangProto()
    q3.name = 'SliceQL'
    q3.parameters['start'] = 3
    q3.parameters['end'] = 4
    q3.priority = 2
    r = Request()
    r.queryset.extend([q1, q2, q3])
    assert isinstance(r.queryset, Sequence)
    for idx, q in enumerate(r.queryset):
        assert q.priority == idx
        assert q.parameters['start'] == 3
        assert q.parameters['end'] == 4

    # q1 and q2 refer to the same
    assert len({id(q) for q in r.queryset}) == 2

    r2 = Request()
    r2.queryset.extend(r.queryset)
    assert len({id(q) for q in r2.queryset}) == 2

    r = Request()
    r.queryset.append(q1)
    r.queryset.append(q2)
    r.queryset.append(q3)
    for idx, q in enumerate(r.queryset):
        assert q.priority == idx
        assert q.parameters['start'] == 3
        assert q.parameters['end'] == 4

    with pytest.raises(TypeError):
        r.queryset.extend(1)


@pytest.mark.parametrize('typ,pb_typ', [('train', jina_pb2.RequestProto.TrainRequestProto),
                                        ('index', jina_pb2.RequestProto.IndexRequestProto),
                                        ('search', jina_pb2.RequestProto.SearchRequestProto),
                                        ('control', jina_pb2.RequestProto.ControlRequestProto)])
def test_empty_request_type(typ, pb_typ):
    r = Request()
    assert r.request_type is None
    with pytest.raises(ValueError):
        print(r.body)

    r.request_type = typ
    assert r._request_type == typ
    assert isinstance(r.body, pb_typ)

@pytest.mark.parametrize('typ,pb_typ', [('index', jina_pb2.RequestProto.IndexRequestProto),
                                        ('search', jina_pb2.RequestProto.SearchRequestProto)])
def test_add_doc_to_type(typ, pb_typ):
    r = Request()
    r.request_type = typ
    for _ in range(10):
        r.docs.append(Document())
        r.groundtruths.append(Document())
    assert len(r.docs) == 10
    assert len(r.groundtruths) == 10
