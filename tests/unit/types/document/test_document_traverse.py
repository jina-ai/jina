import types

import numpy as np
import pytest

from jina import Document, DocumentArray
from jina.clients.request import request_generator
from tests import random_docs

# some random prime number for sanity check
num_docs = 7
num_chunks_per_doc = 11
num_matches_per_doc = 3
num_matches_per_chunk = 5


@pytest.fixture
def doc_req():
    """Build a dummy request that has docs """
    ds = list(random_docs(num_docs, num_chunks_per_doc))
    # add some random matches
    for d in ds:
        for _ in range(num_matches_per_doc):
            d.matches.append(Document(content='hello'))
        for c in d.chunks:
            for _ in range(num_matches_per_chunk):
                c.matches.append(Document(content='world'))
    req = list(request_generator('/', ds))[0]
    yield req


def test_traverse_type(doc_req):
    ds = doc_req.docs.traverse(['r'])
    assert isinstance(ds, types.GeneratorType)
    assert isinstance(list(ds)[0], DocumentArray)


def test_traverse_empty_type(doc_req):
    ds = doc_req.docs.traverse([])
    assert isinstance(ds, types.GeneratorType)
    assert len(list(ds)) == 0


def test_traverse_root(doc_req):
    ds = list(doc_req.docs.traverse(['r']))
    assert len(ds) == 1
    assert len(ds[0]) == num_docs


def test_traverse_chunk(doc_req):
    ds = list(doc_req.docs.traverse(['c']))
    assert len(ds) == num_docs
    assert len(ds[0]) == num_chunks_per_doc


def test_traverse_root_plus_chunk(doc_req):
    ds = list(doc_req.docs.traverse(['c', 'r']))
    assert len(ds) == num_docs + 1
    assert len(ds[0]) == num_chunks_per_doc
    assert len(ds[-1]) == num_docs


def test_traverse_chunk_plus_root(doc_req):
    ds = list(doc_req.docs.traverse(['r', 'c']))
    assert len(ds) == 1 + num_docs
    assert len(ds[-1]) == num_chunks_per_doc
    assert len(ds[0]) == num_docs


def test_traverse_match(doc_req):
    ds = list(doc_req.docs.traverse(['m']))
    assert len(ds) == num_docs
    assert len(ds[0]) == num_matches_per_doc


def test_traverse_match_chunk(doc_req):
    ds = list(doc_req.docs.traverse(['cm']))
    assert len(ds) == num_docs * num_chunks_per_doc
    assert len(ds[0]) == num_matches_per_chunk


def test_traverse_root_match_chunk(doc_req):
    ds = list(doc_req.docs.traverse(['r', 'c', 'm', 'cm']))
    assert len(ds) == 1 + num_docs + num_docs + num_docs * num_chunks_per_doc


def test_traverse_flatten_embedding(doc_req):
    flattened_results = doc_req.docs.traverse_flat(['r', 'c'])
    ds = np.stack(flattened_results.get_attributes('embedding'))
    assert ds.shape == (num_docs + num_chunks_per_doc * num_docs, 10)


def test_traverse_flatten_root(doc_req):
    ds = list(doc_req.docs.traverse_flat(['r']))
    assert len(ds) == num_docs


def test_traverse_flatten_chunk(doc_req):
    ds = list(doc_req.docs.traverse_flat(['c']))
    assert len(ds) == num_docs * num_chunks_per_doc


def test_traverse_flatten_root_plus_chunk(doc_req):
    ds = list(doc_req.docs.traverse_flat(['c', 'r']))
    assert len(ds) == num_docs + num_docs * num_chunks_per_doc


def test_traverse_flatten_match(doc_req):
    ds = list(doc_req.docs.traverse_flat(['m']))
    assert len(ds) == num_docs * num_matches_per_doc


def test_traverse_flatten_match_chunk(doc_req):
    ds = list(doc_req.docs.traverse_flat(['cm']))
    assert len(ds) == num_docs * num_chunks_per_doc * num_matches_per_chunk


def test_traverse_flatten_root_match_chunk(doc_req):
    ds = list(doc_req.docs.traverse_flat(['r', 'c', 'm', 'cm']))
    assert (
        len(ds)
        == num_docs
        + num_chunks_per_doc * num_docs
        + num_matches_per_doc * num_docs
        + num_docs * num_chunks_per_doc * num_matches_per_chunk
    )


def test_traverse_flattened_per_path_embedding(doc_req):
    flattened_results = list(doc_req.docs.traverse_flat_per_path(['r', 'c']))
    ds = np.stack(flattened_results[0].get_attributes('embedding'))
    assert ds.shape == (num_docs, 10)

    ds = np.stack(flattened_results[1].get_attributes('embedding'))
    assert ds.shape == (num_docs * num_chunks_per_doc, 10)


def test_traverse_flattened_per_path_root(doc_req):
    ds = list(doc_req.docs.traverse_flat_per_path(['r']))
    assert len(ds[0]) == num_docs


def test_traverse_flattened_per_path_chunk(doc_req):
    ds = list(doc_req.docs.traverse_flat_per_path(['c']))
    assert len(ds[0]) == num_docs * num_chunks_per_doc


def test_traverse_flattened_per_path_root_plus_chunk(doc_req):
    ds = list(doc_req.docs.traverse_flat_per_path(['c', 'r']))
    assert len(ds[0]) == num_docs * num_chunks_per_doc
    assert len(ds[1]) == num_docs


def test_traverse_flattened_per_path_match(doc_req):
    ds = list(doc_req.docs.traverse_flat_per_path(['m']))
    assert len(ds[0]) == num_docs * num_matches_per_doc


def test_traverse_flattened_per_path_match_chunk(doc_req):
    ds = list(doc_req.docs.traverse_flat_per_path(['cm']))
    assert len(ds[0]) == num_docs * num_chunks_per_doc * num_matches_per_chunk


def test_traverse_flattened_per_path_root_match_chunk(doc_req):
    ds = list(doc_req.docs.traverse_flat_per_path(['r', 'c', 'm', 'cm']))
    assert len(ds[0]) == num_docs
    assert len(ds[1]) == num_chunks_per_doc * num_docs
    assert len(ds[2]) == num_matches_per_doc * num_docs
    assert len(ds[3]) == num_docs * num_chunks_per_doc * num_matches_per_chunk


def test_docuset_traverse_over_iterator_HACKY():
    # HACKY USAGE DO NOT RECOMMEND: can also traverse over "runtime"-documentarray
    ds = DocumentArray(random_docs(num_docs, num_chunks_per_doc)).traverse(['r'])
    assert len(list(list(ds)[0])) == num_docs

    ds = DocumentArray(random_docs(num_docs, num_chunks_per_doc)).traverse(['c'])
    ds = list(ds)
    assert len(ds) == num_docs
    assert len(ds[0]) == num_chunks_per_doc


def test_docuset_traverse_over_iterator_CAVEAT():
    # HACKY USAGE's CAVEAT: but it can not iterate over an iterator twice
    ds = DocumentArray(random_docs(num_docs, num_chunks_per_doc)).traverse(['r', 'c'])
    # note that random_docs is a generator and can be only used once,
    # therefore whoever comes first wil get iterated, and then it becomes empty
    assert len(list(ds)) == 1 + num_docs

    ds = DocumentArray(random_docs(num_docs, num_chunks_per_doc)).traverse(['c', 'r'])
    assert len(list(ds)) == num_docs + 1


def test_doc_iter_method():
    ds = list(random_docs(10))

    for d in DocumentArray(ds):
        assert d.text == 'hello world'

    for d in DocumentArray(ds).traverse_flat(['c', 'r']):
        d.text = 'modified'

    for d in DocumentArray(ds):
        assert d.text == 'modified'
