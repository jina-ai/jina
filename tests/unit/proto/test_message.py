import pytest

from jina.clients.python.request import _generate
from jina.peapods.zmq import add_envelope
from jina.proto import jina_pb2
from jina.proto.message import LazyRequest, _trigger_fields, LazyMessage
from tests import random_docs


@pytest.mark.parametrize('field', _trigger_fields.difference({'command', 'args', 'flush'}))
def test_lazy_access(field):
    reqs = (LazyRequest(r.SerializeToString(), False) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used

        # access r.train
        print(getattr(r, field))

        # now it is read
        assert r.is_used


def test_multiple_access():
    reqs = [LazyRequest(r.SerializeToString(), False) for r in _generate(random_docs(10))]
    for r in reqs:
        assert not r.is_used
        assert r
        assert not r.is_used

    for r in reqs:
        assert not r.is_used
        assert r.index
        assert r.is_used


def test_lazy_nest_access():
    reqs = (LazyRequest(r.SerializeToString(), False) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.docs[0].id = '1'
        # now it is read
        assert r.is_used


def test_lazy_append_access():
    reqs = (LazyRequest(r.SerializeToString(), False) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.docs.append(jina_pb2.Document())
        # now it is read
        assert r.is_used


def test_lazy_clear_access():
    reqs = (LazyRequest(r.SerializeToString(), False) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.ClearField('index')
        # now it is read
        assert r.is_used


def test_lazy_nested_clear_access():
    reqs = (LazyRequest(r.SerializeToString(), False) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.is_used
        # write access r.train
        r.index.ClearField('docs')
        # now it is read
        assert r.is_used


def test_lazy_msg_access():
    reqs = [LazyMessage(add_envelope(r, 'test', '123').envelope.SerializeToString(),
                        r.SerializeToString()) for r in _generate(random_docs(10))]
    for r in reqs:
        assert not r.request.is_used
        assert r.envelope
        assert len(r.dump()) == 2
        assert not r.request.is_used

    for r in reqs:
        assert not r.request.is_used
        assert r.request
        assert len(r.dump()) == 2
        assert not r.request.is_used

    for r in reqs:
        assert not r.request.is_used
        assert r.request.index.docs
        assert len(r.dump()) == 2
        assert r.request.is_used
