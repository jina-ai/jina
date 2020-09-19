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


def test_only_granularity():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        adjacency_range=(0, 0),
        granularity_range=(0, 2),
        recur_on=["chunks"]
    )
    driver._traverse_apply(docs)
    assert len(docs) == 1
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


def test_only_adjacency():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        adjacency_range=(0, 2),
        granularity_range=(0, 0),
        recur_on=["matches"]
    )
    driver._traverse_apply(docs)
    assert len(docs) == 1
    assert len(docs[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches) == 1
    assert len(docs[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches) == 1
    assert len(docs[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


def test_adjacency_chunks():
    """
    This combination of `range` and `recur_on` will only `_apply_all` to the root node.
    Thus, the remaining document structure should still be intact.
    In practice this combination should not be chosen, anyhow it nicely demonstrates the behaviour.
    """
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        adjacency_range=(0, 1),
        granularity_range=(0, 0),
        recur_on=["chunks"]
    )
    driver._traverse_apply(docs)
    assert len(docs) == 1
    assert len(docs[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


def test_granularity_matches():
    """
    This combination of `range` and `recur_on` will only `_apply_all` to the root node.
    Thus, the remaining document structure should still be intact.
    In practice this combination should not be chosen, anyhow it nicely demonstrates the behaviour.
    """
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        adjacency_range=(0, 0),
        granularity_range=(0, 1),
        recur_on=["matches"]
    )
    driver._traverse_apply(docs)
    assert len(docs) == 1
    assert len(docs[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].matches[0].matches[0].chunks) == DOCUMENTS_PER_LEVEL


def test_both_from_0():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        adjacency_range=(0, 2),
        granularity_range=(0, 2),
        recur_on=["chunks", "matches"]
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


def test_adjacency0_granularity1():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        adjacency_range=(0, 2),
        granularity_range=(1, 2),
        recur_on=["chunks", "matches"]
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


def test_adjacency1_granularity1():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        adjacency_range=(1, 2),
        granularity_range=(1, 2),
        recur_on=["chunks", "matches"]
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


@pytest.mark.skip('this test will fail on v0.5.5 because the way of traversing is limited')
def test_selection():
    docs = build_docs()
    driver = SliceQL(
        start=0,
        end=1,
        granularity_range=(1, 1),
        adjacency_range=(2, 2),
        recur_on=['matches', ]
    )
    driver._traverse_apply(docs)
    # check the granularity and adjacency
    assert docs[0].chunks[0].matches[0].matches[0].granularity == 1
    assert docs[0].chunks[0].matches[0].matches[0].adjacency == 2
    assert len(docs[0].chunks[0].matches[0].matches) == 1
    # check the granularity and adjacency
    assert docs[0].matches[0].chunks[0].matches[0].granularity == 1
    assert docs[0].matches[0].chunks[0].matches[0].adjacency == 2
    # For the chunks of the matches, the matches of these chunks are not effected by the apply()
    assert len(docs[0].matches[0].chunks[0].matches) == 1


@pytest.mark.skip('this test will fail on v0.5.5 because the way of traversing is limited')
def test_traverse_apply():
    docs = build_docs()
    doc = docs[0]
    doc.ClearField('chunks')
    docs = [doc, ]
    driver = SliceQL(
        start=0,
        end=1,
        adjacency_range=(2, 2),
        granularity_range=(1, 1),
        recur_on=["matches", ]
    )
    # check we have a match with (g=1, a=2)
    assert docs[0].matches[0].chunks[0].matches[0].granularity == 1
    assert docs[0].matches[0].chunks[0].matches[0].adjacency == 2
    # the following part will cause IndexError
    driver._traverse_apply(docs)
    assert len(docs[0].matches[0].chunks[0].matches) == 1
