import os

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
            iterate_build(dc, current_granularity + 1, max_granularity, current_adjacency, max_adjacency)
    if current_adjacency < max_adjacency:
        for i in range(DOCUMENTS_PER_LEVEL):
            dc = d.matches.add()
            dc.granularity = current_granularity
            dc.adjacency = current_adjacency + 1
            dc.id = i
            iterate_build(dc, current_granularity, max_granularity, current_adjacency + 1, max_adjacency)


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


def test_adjacency_on_chunks():
    docs = build_docs()
    doc = docs[0]
    doc.ClearField('matches')
    docs = [doc, ]
    driver = SliceQL(
        start=0,
        end=1,
        adjacency_range=(1, 1),
        granularity_range=(1, 2),
        recur_on=["chunks", ]
    )
    driver._traverse_apply(docs)
    assert len(docs) == 1
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
    assert len(docs[0].chunks[0].matches) == DOCUMENTS_PER_LEVEL
