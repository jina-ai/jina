from collections import Iterator

import pytest

from jina import Document
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
            d.matches.add(Document(content='hello'))
        for c in d.chunks:
            for _ in range(num_matches_per_chunk):
                c.matches.add(Document(content='world'))
    req = list(request_generator(ds))[0]
    yield req


def test_traverse_type(doc_req):
    assert isinstance(doc_req.docs.traverse(['r']), Iterator)


def test_traverse_empty_type(doc_req):
    assert isinstance(doc_req.docs.traverse([]), Iterator)
    assert len(list(doc_req.docs.traverse([]))) == 0


def test_traverse_root(doc_req):
    ds = list(doc_req.docs.traverse(['r']))
    assert len(ds) == num_docs


def test_traverse_chunk(doc_req):
    ds = list(doc_req.docs.traverse(['c']))
    assert len(ds) == num_docs * num_chunks_per_doc


def test_traverse_root_plus_chunk(doc_req):
    ds = list(doc_req.docs.traverse(['c', 'r']))
    assert len(ds) == num_docs + num_docs * num_chunks_per_doc


def test_traverse_match(doc_req):
    ds = list(doc_req.docs.traverse(['m']))
    assert len(ds) == num_docs * num_matches_per_doc


def test_traverse_match_chunk(doc_req):
    ds = list(doc_req.docs.traverse(['cm']))
    assert len(ds) == num_docs * num_chunks_per_doc * num_matches_per_chunk


def test_traverse_root_match_chunk(doc_req):
    ds = list(doc_req.docs.traverse(['r', 'c', 'm', 'cm']))
    assert (len(ds) == num_docs + num_chunks_per_doc * num_docs +
            num_matches_per_doc * num_docs + num_docs * num_chunks_per_doc * num_matches_per_chunk)
