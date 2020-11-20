import sys

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
    r.extend_queryset([q1, q2, q3])
    for idx, q in enumerate(r.queryset):
        assert q.priority == idx
        assert q.parameters['start'] == 3
        assert q.parameters['end'] == 4

    r = Request()
    r.extend_queryset(q1)
    r.extend_queryset(q2)
    r.extend_queryset(q3)
    for idx, q in enumerate(r.queryset):
        assert q.priority == idx
        assert q.parameters['start'] == 3
        assert q.parameters['end'] == 4

    with pytest.raises(TypeError):
        r.extend_queryset(1)
