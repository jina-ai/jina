import pytest
import numpy as np
import random

from jina.drivers.helper import array2pb, pb2array, pb_obj2dict, add_route, extract_docs, DocGroundTruthPair
from jina.proto import jina_pb2


@pytest.mark.parametrize(
    'type', ['float32', 'float64', 'uint8']
)
@pytest.mark.repeat(10)
def test_array_protobuf_conversions(type):
    random_array = np.random.rand(random.randrange(0, 50), random.randrange(0, 20)).astype(type)
    np.testing.assert_almost_equal(pb2array(array2pb(random_array, None)), random_array)


@pytest.mark.parametrize(
    'quantize, type', [('fp16', 'float32'), ('fp16', 'float64'), ('uint8', 'uint8')],
)
@pytest.mark.repeat(10)
def test_array_protobuf_conversions_with_quantize(quantize, type):
    random_array = np.random.rand(random.randrange(0, 50), random.randrange(0, 20)).astype(type)
    np.testing.assert_almost_equal(pb2array(array2pb(random_array, quantize)), random_array, decimal=2)


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
    envelope = jina_pb2.Envelope()
    add_route(envelope, 'name', 'identity')
    assert len(envelope.routes) == 1
    assert envelope.routes[0].pod == 'name'
    assert envelope.routes[0].pod_id == 'identity'


def test_extract_docs():
    d = jina_pb2.Document()

    contents, docs_pts, bad_doc_ids = extract_docs([d], embedding=True)
    assert len(bad_doc_ids) > 0
    assert contents is None

    vec = np.random.random([2, 2])
    d.embedding.CopyFrom(array2pb(vec))
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

    pair = DocGroundTruthPair(doc, gt)
    assert len(pair.chunks) == 3
    assert len(pair.matches) == 3

    for chunk_pair in pair.chunks:
        assert chunk_pair.doc.granularity == 1
        assert chunk_pair.groundtruth.granularity == 1

    for match_pair in pair.matches:
        assert match_pair.doc.adjacency == 1
        assert match_pair.groundtruth.adjacency == 1
