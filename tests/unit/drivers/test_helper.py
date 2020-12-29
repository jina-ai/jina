import random

import numpy as np
import pytest

from jina import Document, DocumentSet
from jina.proto import jina_pb2
from jina.types.message import Message
from jina.types.ndarray.generic import NdArray


@pytest.fixture(scope='function')
def document():
    with Document() as doc:
        doc.text = 'this is text'
        doc.tags['id'] = 'id in tags'
        doc.tags['inner_dict'] = {'id': 'id in inner_dict'}
        with Document() as chunk:
            chunk.text = 'text in chunk'
            chunk.tags['id'] = 'id in chunk tags'
        doc.chunks.add(chunk)
    return doc


@pytest.mark.parametrize(
    'type', ['float32', 'float64', 'uint8']
)
@pytest.mark.repeat(10)
def test_array_protobuf_conversions(type):
    random_array = np.random.rand(random.randrange(0, 50), random.randrange(0, 20)).astype(type)
    d = NdArray()
    d.value = random_array
    np.testing.assert_almost_equal(d.value, random_array)


@pytest.mark.parametrize(
    'quantize, type', [('fp16', 'float32'), ('fp16', 'float64'), ('uint8', 'uint8')],
)
@pytest.mark.repeat(10)
def test_array_protobuf_conversions_with_quantize(quantize, type):
    random_array = np.random.rand(random.randrange(0, 50), random.randrange(0, 20)).astype(type)
    d = NdArray(quantize=quantize)
    d.value = random_array
    np.testing.assert_almost_equal(d.value, random_array, decimal=2)


def test_pb_obj2dict(document):
    res = document.get_attrs('text', 'tags', 'chunks')
    assert res['text'] == 'this is text'
    assert res['tags']['id'] == 'id in tags'
    assert res['tags']['inner_dict']['id'] == 'id in inner_dict'
    rcs = list(res['chunks'])
    assert len(rcs) == 1
    assert isinstance(rcs[0], Document)
    assert rcs[0].text == 'text in chunk'
    assert rcs[0].tags['id'] == 'id in chunk tags'


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

    contents, docs_pts, bad_docs = DocumentSet([d]).all_embeddings
    assert len(bad_docs) > 0
    assert contents is None

    vec = np.random.random([2, 2])
    d.embedding = vec
    contents, docs_pts, bad_docs = DocumentSet([d]).all_embeddings
    assert len(bad_docs) == 0
    np.testing.assert_equal(contents[0], vec)
