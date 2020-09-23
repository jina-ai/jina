import os
import pytest

from jina.proto import jina_pb2

cur_dir = os.path.dirname(os.path.abspath(__file__))


from jina.drivers.querylang.slice import SliceQL

cur_dir = os.path.dirname(os.path.abspath(__file__))

DOCUMENTS_PER_LEVEL = 2


def build_docs():
    """ Builds up a complete chunk-match structure, with a depth of 2 in both directions recursively. """
    docs = []
    for base_id in range(DOCUMENTS_PER_LEVEL):
        d = jina_pb2.Document()
        d.granularity = 0
        d.adjacency = 0
        d.id = base_id
        docs.append(d)
        iterate_build(d, 0, 2, 0, 2)
    return docs


def iterate_build(d, current_granularity, max_granularity, current_adjacency, max_adjacency):
    if current_granularity < max_granularity:
        for i in range(DOCUMENTS_PER_LEVEL):
            dc = d.chunks.add()
            dc.granularity = current_granularity + 1
            dc.adjacency = current_adjacency
            dc.id = i
            iterate_build(dc, dc.granularity, max_granularity, dc.adjacency, max_adjacency)
    if current_adjacency < max_adjacency:
        for i in range(DOCUMENTS_PER_LEVEL):
            dc = d.matches.add()
            dc.granularity = current_granularity
            dc.adjacency = current_adjacency + 1
            dc.id = i
            iterate_build(dc, dc.granularity, max_granularity, dc.adjacency, max_adjacency)


@pytest.mark.skip(reason='this is a test for the proposed new flow design')
def test_only_root():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        traversal_paths=['r']
    )
    driver._traverse_apply(docs)
    assert len(docs) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


@pytest.mark.skip(reason='this is a test for the proposed new flow design')
def test_only_matches():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        traversal_paths=['m']
    )
    driver._traverse_apply(docs)
    assert len(docs) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches) == 1
    assert len(docs[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


@pytest.mark.skip(reason='this is a test for the proposed new flow design')
def test_only_chunks():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        traversal_paths=['c']
    )
    driver._traverse_apply(docs)
    assert len(docs) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


@pytest.mark.skip(reason='this is a test for the proposed new flow design')
def test_match_chunk():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        traversal_paths=['mc']
    )
    driver._traverse_apply(docs)
    assert len(docs) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].chunks) == 1
    assert len(docs[0].matches[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


@pytest.mark.skip(reason='this is a test for the proposed new flow design')
def test_chunk_match():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        traversal_paths=['cm']
    )
    driver._traverse_apply(docs)
    assert len(docs) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == 1
    assert len(docs[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


@pytest.mark.skip(reason='this is a test for the proposed new flow design')
def test_multi_paths():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        traversal_paths=['cc', 'mm']
    )
    driver._traverse_apply(docs)
    assert len(docs) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].chunks) == 1
    assert len(docs[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches) == 1
    assert len(docs[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


@pytest.mark.skip(reason='this is a test for the proposed new flow design')
def test_both_from_0():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        traversal_paths=['r', 'c', 'm', 'cc', 'mm']
    )
    driver._traverse_apply(docs)
    assert len(docs) == 1
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches) == 1
    assert len(docs[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches) == 1
    assert len(docs[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


@pytest.mark.skip(reason='this is a test for the proposed new flow design')
def test_adjacency0_granularity1():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        traversal_paths=['c', 'cc', 'cm', 'cmm']
    )
    driver._traverse_apply(docs)
    assert len(docs) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == 1
    assert len(docs[0].chunks[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches[0].matches) == 1
    assert len(docs[0].chunks[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


@pytest.mark.skip(reason='this is a test for the proposed new flow design')
def test_adjacency1_granularity1():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        traversal_paths=['cm', 'cmm' 'mcc']
    )
    driver._traverse_apply(docs)
    assert len(docs) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == 1
    assert len(docs[0].chunks[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches[0].matches) == 1
    assert len(docs[0].chunks[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].chunks) == 1
    assert len(docs[0].matches[0].chunks[0].chunks) == 1
    assert len(docs[0].matches[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


@pytest.mark.skip(reason='this is a test for the proposed new flow design')
def test_selection():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        traversal_paths=['cmm', 'mcm']
    )
    driver._traverse_apply(docs)
    assert docs[0].chunks[0].matches[0].matches[0].granularity == 1
    assert docs[0].chunks[0].matches[0].matches[0].adjacency == 2
    assert len(docs[0].chunks[0].matches[0].matches) == 1
    assert docs[0].matches[0].chunks[0].matches[0].granularity == 1
    assert docs[0].matches[0].chunks[0].matches[0].adjacency == 2
    assert len(docs[0].matches[0].chunks[0].matches) == 1


@pytest.mark.skip(reason='this is a test for the proposed new flow design')
def test_traverse_apply():
    docs = build_docs()
    doc = docs[0]
    doc.ClearField('chunks')
    docs = [doc, ]
    driver = SliceQL(
        start=0,
        end=1,
        traversal_paths=['mcm']
    )
    assert docs[0].matches[0].chunks[0].matches[0].granularity == 1
    assert docs[0].matches[0].chunks[0].matches[0].adjacency == 2
    driver._traverse_apply(docs)
    assert len(docs[0].matches[0].chunks[0].matches) == 1
