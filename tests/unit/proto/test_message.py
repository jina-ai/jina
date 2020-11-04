import sys

import pytest

from jina.clients.python.request import _generate
from jina.proto import jina_pb2
from jina.proto.jina_pb2 import Envelope
from jina.proto.message import LazyRequest, ProtoMessage
from jina.proto.message.lazyrequest import _trigger_fields
from tests import random_docs


@pytest.mark.parametrize('field', _trigger_fields.difference({'command', 'args', 'flush'}))
def test_lazy_access(field):
    reqs = (LazyRequest(r.SerializeToString(), Envelope()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used

        # access r.train
        print(getattr(r, field))

        # now it is read
        assert r.is_used


def test_multiple_access():
    reqs = [LazyRequest(r.SerializeToString(), Envelope()) for r in _generate(random_docs(10))]
    for r in reqs:
        assert not r.is_used
        assert r
        assert not r.is_used

    for r in reqs:
        assert not r.is_used
        assert r.index
        assert r.is_used


def test_lazy_nest_access():
    reqs = (LazyRequest(r.SerializeToString(), Envelope()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.docs[0].id = '1'
        # now it is read
        assert r.is_used
        assert r.index.docs[0].id == '1'


def test_lazy_change_message_type():
    reqs = (LazyRequest(r.SerializeToString(), Envelope()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.control.command = jina_pb2.Request.ControlRequest.IDLE
        # now it is read
        assert r.is_used
        assert len(r.index.docs) == 0


def test_lazy_append_access():
    reqs = (LazyRequest(r.SerializeToString(), Envelope()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.docs.append(jina_pb2.Document())
        # now it is read
        assert r.is_used


def test_lazy_clear_access():
    reqs = (LazyRequest(r.SerializeToString(), Envelope()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.ClearField('index')
        # now it is read
        assert r.is_used


def test_lazy_nested_clear_access():
    reqs = (LazyRequest(r.SerializeToString(), Envelope()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.index.ClearField('docs')
        # now it is read
        assert r.is_used


def test_lazy_msg_access():
    reqs = [ProtoMessage(None, r.SerializeToString(), 'test', '123',
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
    reqs = [ProtoMessage(None, r, 'test', '123') for r in _generate(random_docs(10))]
    for r in reqs:
        assert r.size == 0
        assert sys.getsizeof(r.envelope.SerializeToString())
        assert sys.getsizeof(r.request.SerializeToString())
        assert len(r.dump()) == 3
        assert r.size > sys.getsizeof(r.envelope.SerializeToString()) \
               + sys.getsizeof(r.request.SerializeToString())


def test_lazy_request_fields():
    reqs = (LazyRequest(r.SerializeToString(), Envelope()) for r in _generate(random_docs(10)))
    for r in reqs:
        assert list(r.DESCRIPTOR.fields_by_name.keys())
