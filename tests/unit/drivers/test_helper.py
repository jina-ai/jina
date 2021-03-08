import random

import numpy as np
import pytest

from jina import Document, DocumentSet
from jina.proto import jina_pb2
from jina.types.message import Message
from jina.types.ndarray.generic import NdArray


@pytest.mark.parametrize('proto_type', ['float32', 'float64', 'uint8'])
@pytest.mark.repeat(10)
def test_array_protobuf_conversions(proto_type):
    random_array = np.random.rand(
        random.randrange(0, 50), random.randrange(0, 20)
    ).astype(proto_type)
    d = NdArray()
    d.value = random_array
    np.testing.assert_almost_equal(d.value, random_array)


@pytest.mark.parametrize(
    'quantize, proto_type',
    [('fp16', 'float32'), ('fp16', 'float64'), ('uint8', 'uint8')],
)
@pytest.mark.repeat(10)
def test_array_protobuf_conversions_with_quantize(quantize, proto_type):
    random_array = np.random.rand(
        random.randrange(0, 50), random.randrange(0, 20)
    ).astype(proto_type)
    d = NdArray(quantize=quantize)
    d.value = random_array
    np.testing.assert_almost_equal(d.value, random_array, decimal=2)


def test_add_route():
    r = jina_pb2.RequestProto()
    r.control.command = jina_pb2.RequestProto.ControlRequestProto.IDLE
    msg = Message(None, r, pod_name='test1', identity='sda')
    msg.add_route('name', 'identity')
    assert len(msg.envelope.routes) == 2
    assert msg.envelope.routes[1].pod == 'name'
    assert msg.envelope.routes[1].pod_id == 'identity'


def test_extract_docs():
    d = Document()

    contents, docs_pts = DocumentSet([d]).all_embeddings
    assert contents is None

    vec = np.random.random([2, 2])
    d.embedding = vec
    contents, docs_pts = DocumentSet([d]).all_embeddings
    np.testing.assert_equal(contents[0], vec)
