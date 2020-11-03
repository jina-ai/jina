import random

import numpy as np
import pytest

from jina.drivers.helper import pb_obj2dict, extract_docs, DocGroundtruthPair
from jina.proto import jina_pb2
from jina.proto.message import ProtoMessage
from jina.proto.ndarray.generic import GenericNdArray


@pytest.mark.parametrize(
    'type', ['float32', 'float64', 'uint8']
)
@pytest.mark.repeat(10)
def test_array_protobuf_conversions(type):
    random_array = np.random.rand(random.randrange(0, 50), random.randrange(0, 20)).astype(type)
    d = GenericNdArray()
    d.value = random_array
    np.testing.assert_almost_equal(d.value, random_array)


@pytest.mark.parametrize(
    'quantize, type', [('fp16', 'float32'), ('fp16', 'float64'), ('uint8', 'uint8')],
)
@pytest.mark.repeat(10)
def test_array_protobuf_conversions_with_quantize(quantize, type):
    random_array = np.random.rand(random.randrange(0, 50), random.randrange(0, 20)).astype(type)
    d = GenericNdArray(quantize=quantize)
    d.value = random_array
    np.testing.assert_almost_equal(d.value, random_array, decimal=2)


def test_pb_obj2dict():
    document = jina_pb2.Document()
    document.text = 'this is text'
    document.tags['id'] = 'id in tags'
    document.tags['inner_dict'] = {'id': 'id in inner_dict'}
    chunk = document.chunks.add()
    chunk.text = 'text in chunk'
    chunk.tags['id'] = 'id in chunk tags'
    res = pb_obj2dict(document, ['text', 'tags', 'chunks'])
    assert res['text'] == 'this is text'
    assert res['tags']['id'] == 'id in tags'
    assert res['tags']['inner_dict']['id'] == 'id in inner_dict'
    assert len(res['chunks']) == 1
    assert isinstance(res['chunks'][0], jina_pb2.Document)
    assert res['chunks'][0].text == 'text in chunk'
    assert res['chunks'][0].tags['id'] == 'id in chunk tags'


def test_add_route():
    r = jina_pb2.Request()
    r.control.command = jina_pb2.Request.ControlRequest.IDLE
    msg = ProtoMessage(None, r, pod_name='test1', identity='sda')
    msg.add_route('name', 'identity')
    assert len(msg.envelope.routes) == 2
    assert msg.envelope.routes[1].pod == 'name'
    assert msg.envelope.routes[1].pod_id == 'identity'


def test_extract_docs():
    d = jina_pb2.Document()

    contents, docs_pts, bad_doc_ids = extract_docs([d], embedding=True)
    assert len(bad_doc_ids) > 0
    assert contents is None

    vec = np.random.random([2, 2])
    GenericNdArray(d.embedding).value = vec
    contents, docs_pts, bad_doc_ids = extract_docs([d], embedding=True)
    assert len(bad_doc_ids) == 0
    np.testing.assert_equal(contents[0], vec)


def test_docgroundtruth_pair():
    def add_matches(doc: jina_pb2.Document, num_matches):
        for idx in range(num_matches):
            match = doc.matches.add()
            match.adjacency = doc.adjacency + 1

    def add_chunks(doc: jina_pb2.Document, num_chunks):
        for idx in range(num_chunks):
            chunk = doc.chunks.add()
            chunk.granularity = doc.granularity + 1

    doc = jina_pb2.Document()
    gt = jina_pb2.Document()
    add_matches(doc, 3)
    add_matches(gt, 3)
    add_chunks(doc, 3)
    add_chunks(gt, 3)

    pair = DocGroundtruthPair(doc, gt)

    j = 0
    for chunk_pair in pair.chunks:
        assert chunk_pair.doc.granularity == 1
        assert chunk_pair.groundtruth.granularity == 1
        j += 1

    k = 0
    for match_pair in pair.matches:
        assert match_pair.doc.adjacency == 1
        assert match_pair.groundtruth.adjacency == 1
        k += 1

    assert j == 3
    assert k == 3
