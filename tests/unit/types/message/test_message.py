import sys

import pytest

from jina import Document
from jina.clients.request import request_generator
from jina.proto import jina_pb2
from jina.types.message import Message
from jina.types.request import _trigger_fields, Request
from jina.enums import CompressAlgo
from tests import random_docs


@pytest.mark.parametrize(
    'field',
    _trigger_fields.difference({'command', 'args', 'flush', 'propagate', 'targets'}),
)
@pytest.mark.parametrize(
    'algo',
    [None, CompressAlgo.NONE],
)
def test_lazy_access(field, algo):
    reqs = (
        Request(r.SerializeToString(), algo)
        for r in request_generator('/', random_docs(10))
    )
    for r in reqs:
        assert not r.is_decompressed

        # access r.train
        print(getattr(r, field))

        # now it is read
        assert r.is_decompressed


@pytest.mark.parametrize(
    'algo',
    [None, CompressAlgo.NONE],
)
def test_multiple_access(algo):
    reqs = [
        Request(r.SerializeToString(), algo)
        for r in request_generator('/', random_docs(10))
    ]
    for r in reqs:
        assert not r.is_decompressed
        assert r
        assert not r.is_decompressed

    for r in reqs:
        assert not r.is_decompressed
        assert r.data
        assert r.is_decompressed


@pytest.mark.parametrize(
    'algo',
    [None, CompressAlgo.NONE],
)
def test_lazy_nest_access(algo):
    reqs = (
        Request(r.SerializeToString(), algo)
        for r in request_generator('/', random_docs(10))
    )
    for r in reqs:
        assert not r.is_decompressed
        # write access r.train
        r.docs[0].id = '1' * 16
        # now it is read
        assert r.is_decompressed
        assert r.data.docs[0].id == '1' * 16


@pytest.mark.parametrize(
    'algo',
    [None, CompressAlgo.NONE],
)
def test_lazy_change_message_type(algo):
    reqs = (
        Request(r.SerializeToString(), algo)
        for r in request_generator('/', random_docs(10))
    )
    for r in reqs:
        assert not r.is_decompressed
        # write access r.train
        r.control.command = jina_pb2.RequestProto.ControlRequestProto.IDLE
        # now it is read
        assert r.is_decompressed
        assert len(r.data.docs) == 0


@pytest.mark.parametrize(
    'algo',
    [None, CompressAlgo.NONE],
)
def test_lazy_append_access(algo):
    reqs = (
        Request(r.SerializeToString(), algo)
        for r in request_generator('/', random_docs(10))
    )
    for r in reqs:
        assert not r.is_decompressed
        r = Request().as_typed_request('data')
        # write access r.train
        r.docs.append(Document())
        # now it is read
        assert r.is_decompressed


@pytest.mark.parametrize(
    'algo',
    [None, CompressAlgo.NONE],
)
def test_lazy_clear_access(algo):
    reqs = (
        Request(r.SerializeToString(), algo)
        for r in request_generator('/', random_docs(10))
    )
    for r in reqs:
        assert not r.is_decompressed
        # write access r.train
        r.ClearField('data')
        # now it is read
        assert r.is_decompressed


@pytest.mark.parametrize(
    'algo',
    [None, CompressAlgo.NONE],
)
def test_lazy_nested_clear_access(algo):
    reqs = (
        Request(r.SerializeToString(), algo)
        for r in request_generator('/', random_docs(10))
    )
    for r in reqs:
        assert not r.is_decompressed
        # write access r.train
        r.data.ClearField('docs')
        # now it is read
        assert r.is_decompressed


def test_lazy_msg_access():
    # this test does not make much sense, when `message` is instantiated without `envelope`, the `request` header is accessed and therefore decompressed
    messages = [
        Message(
            None,
            r.SerializeToString(),
            'test',
            '123',
            request_id='123',
            request_type='DataRequest',
        )
        for r in request_generator('/', random_docs(10))
    ]
    for m in messages:
        assert m.request.is_decompressed
        assert m.envelope
        assert len(m.dump()) == 3
        assert m.request.is_decompressed

    for m in messages:
        assert m.request.is_decompressed
        assert m.request
        assert len(m.dump()) == 3
        assert m.request.is_decompressed

    for m in messages:
        assert m.request.is_decompressed
        assert m.request.data.docs
        assert len(m.dump()) == 3
        assert m.request.is_decompressed


def test_lazy_msg_access_with_envelope():
    envelope_proto = jina_pb2.EnvelopeProto()
    envelope_proto.compression.algorithm = 'NONE'
    envelope_proto.request_type = 'DataRequest'
    messages = [
        Message(
            envelope_proto,
            r.SerializeToString(),
        )
        for r in request_generator('/', random_docs(10))
    ]
    for m in messages:
        assert not m.request.is_decompressed
        assert m.envelope
        assert len(m.dump()) == 3
        assert not m.request.is_decompressed
        assert m.request._pb_body is None
        assert m.request._buffer is not None
        assert m.proto
        assert m.request.is_decompressed
        assert m.request._pb_body is not None
        assert m.request._buffer is None


def test_message_size():
    reqs = [
        Message(None, r, 'test', '123') for r in request_generator('/', random_docs(10))
    ]
    for r in reqs:
        assert r.size == 0
        assert sys.getsizeof(r.envelope.SerializeToString())
        assert sys.getsizeof(r.request.SerializeToString())
        assert len(r.dump()) == 3
        assert r.size > sys.getsizeof(r.envelope.SerializeToString()) + sys.getsizeof(
            r.request.SerializeToString()
        )


@pytest.mark.parametrize(
    'algo',
    [None, CompressAlgo.NONE],
)
def test_lazy_request_fields(algo):
    reqs = (
        Request(r.SerializeToString(), algo)
        for r in request_generator('/', random_docs(10))
    )
    for r in reqs:
        assert list(r.DESCRIPTOR.fields_by_name.keys())


@pytest.mark.parametrize(
    'typ,pb_typ',
    [
        ('data', jina_pb2.RequestProto.DataRequestProto),
        ('control', jina_pb2.RequestProto.ControlRequestProto),
    ],
)
def test_empty_request_type(typ, pb_typ):
    r = Request()
    assert r.request_type is None
    with pytest.raises(ValueError):
        print(r.body)

    r = r.as_typed_request(typ)
    assert r._request_type == typ
    assert isinstance(r.body, pb_typ)


@pytest.mark.parametrize(
    'typ,pb_typ',
    [
        ('data', jina_pb2.RequestProto.DataRequestProto),
    ],
)
def test_add_doc_to_type(typ, pb_typ):
    r = Request().as_typed_request(typ)
    for _ in range(10):
        r.docs.append(Document())
        r.groundtruths.append(Document())
    assert len(r.docs) == 10
    assert len(r.groundtruths) == 10
