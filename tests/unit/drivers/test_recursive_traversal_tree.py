import os

from jina.drivers import BaseRecursiveDriver
from jina.proto import jina_pb2

cur_dir = os.path.dirname(os.path.abspath(__file__))

DOCUMENTS_PER_LEVEL = 1


class AppendOneChunkTwoMatchesCrafter(BaseRecursiveDriver):

    def _apply_all(self, docs, *args, **kwargs) -> None:
        for doc in docs:
            add_chunk(doc)
            add_match(doc)
            add_match(doc)


def add_chunk(doc):
    chunk = doc.chunks.add()
    chunk.granularity = doc.granularity + 1
    chunk.adjacency = doc.adjacency
    return chunk


def add_match(doc):
    match = doc.matches.add()
    match.granularity = doc.granularity
    match.adjacency = doc.adjacency + 1
    return match


def build_docs():
    """ Builds up a complete chunk-match structure, with a depth of 2 in both directions recursively. """
    max_granularity = 2
    max_adjacency = 2

    def iterate_build(document, current_granularity, current_adjacency):
        if current_granularity < max_granularity:
            for i in range(DOCUMENTS_PER_LEVEL):
                chunk = add_chunk(document)
                iterate_build(chunk, chunk.granularity, chunk.adjacency)
        if current_adjacency < max_adjacency:
            for i in range(DOCUMENTS_PER_LEVEL):
                match = add_match(document)
                iterate_build(match, match.granularity, match.adjacency)

    docs = []
    for base_id in range(DOCUMENTS_PER_LEVEL):
        document = jina_pb2.Document()
        document.granularity = 0
        document.adjacency = 0
        docs.append(document)
        iterate_build(document, 0, 0)
    return docs


def apply_traversal_path(traversal_paths):
    docs = build_docs()
    driver = AppendOneChunkTwoMatchesCrafter(traversal_paths=traversal_paths)
    driver._traverse_apply(docs)
    return docs


def test_only_root():
    docs = apply_traversal_path(['r'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 2
    assert len(docs[0].chunks[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks[0].matches) == 1
    assert len(docs[0].chunks[0].matches) == 1
    assert len(docs[0].matches) == 3
    assert len(docs[0].matches[0].chunks) == 1


def test_only_matches():
    docs = apply_traversal_path(['m'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].matches) == 1
    assert len(docs[0].matches) == 1
    assert len(docs[0].matches[0].chunks) == 2
    assert len(docs[0].matches[0].matches) == 3
    assert len(docs[0].matches[0].matches[0].chunks) == 1


def test_only_chunks():
    docs = apply_traversal_path(['c'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks) == 2
    assert len(docs[0].chunks[0].matches) == 3
    assert len(docs[0].matches) == 1
    assert len(docs[0].matches[0].chunks) == 1
    assert len(docs[0].matches[0].matches) == 1
    assert len(docs[0].matches[0].matches[0].chunks) == 1


def test_match_chunk():
    docs = apply_traversal_path(['mc'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].matches) == 1
    assert len(docs[0].matches) == 1
    assert len(docs[0].matches[0].chunks) == 1
    assert len(docs[0].matches[0].chunks[0].chunks) == 2
    assert len(docs[0].matches[0].matches) == 1
    assert len(docs[0].matches[0].matches[0].chunks) == 1


def test_chunk_match():
    docs = apply_traversal_path(['cm'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].matches) == 1
    assert len(docs[0].chunks[0].matches[0].chunks) == 2
    assert len(docs[0].matches) == 1
    assert len(docs[0].matches[0].chunks) == 1
    assert len(docs[0].matches[0].matches) == 1
    assert len(docs[0].matches[0].matches[0].chunks) == 1


def test_multi_paths():
    docs = apply_traversal_path(['cc', 'mm'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].matches) == 1
    assert len(docs[0].chunks[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks[0].chunks) == 1
    assert len(docs[0].matches) == 1
    assert len(docs[0].matches[0].chunks) == 1
    assert len(docs[0].matches[0].matches) == 1
    assert len(docs[0].matches[0].matches[0].chunks) == 2


def test_both_from_0():
    docs = apply_traversal_path(['r', 'c', 'm', 'cc', 'mm'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 2
    assert len(docs[0].chunks[0].chunks) == 2
    assert len(docs[0].chunks[0].chunks[0].matches) == 3
    assert len(docs[0].chunks[0].chunks[0].chunks) == 1  # 0 before traversal
    assert len(docs[0].chunks[0].matches) == 3
    assert len(docs[0].matches) == 3
    assert len(docs[0].matches[0].chunks) == 2
    assert len(docs[0].matches[0].matches) == 3
    assert len(docs[0].matches[0].matches[0].chunks) == 2


def test_both_from_0_upper_case():
    docs = apply_traversal_path(['R', 'C', 'M', 'CC', 'MM'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 2
    assert len(docs[0].chunks[0].chunks) == 2
    assert len(docs[0].chunks[0].chunks[0].matches) == 3
    assert len(docs[0].chunks[0].chunks[0].chunks) == 1  # 0 before traversal
    assert len(docs[0].chunks[0].matches) == 3
    assert len(docs[0].matches) == 3
    assert len(docs[0].matches[0].chunks) == 2
    assert len(docs[0].matches[0].matches) == 3
    assert len(docs[0].matches[0].matches[0].chunks) == 2


def test_adjacency0_granularity1():
    docs = apply_traversal_path(['c', 'cc', 'cm', 'cmm'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks) == 2
    assert len(docs[0].chunks[0].chunks[0].matches) == 3
    assert len(docs[0].chunks[0].matches) == 3
    assert len(docs[0].chunks[0].matches[0].chunks) == 2
    assert len(docs[0].chunks[0].matches[0].matches) == 3
    assert len(docs[0].chunks[0].matches[0].matches[0].chunks) == 2
    assert len(docs[0].matches) == 1
    assert len(docs[0].matches[0].chunks) == 1
    assert len(docs[0].matches[0].matches) == 1
    assert len(docs[0].matches[0].matches[0].chunks) == 1


def test_adjacency1_granularity1():
    docs = apply_traversal_path(['cm', 'cmm', 'mcc'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks) == 1
    assert len(docs[0].chunks[0].chunks[0].matches) == 1
    assert len(docs[0].chunks[0].matches) == 1
    assert len(docs[0].chunks[0].matches[0].chunks) == 2
    assert len(docs[0].chunks[0].matches[0].matches) == 3
    assert len(docs[0].chunks[0].matches[0].matches[0].chunks) == 2
    assert len(docs[0].matches) == 1
    assert len(docs[0].matches[0].chunks) == 1
    assert len(docs[0].matches[0].chunks[0].chunks) == 1
    assert len(docs[0].matches[0].chunks[0].chunks[0].matches) == 3
    assert len(docs[0].matches[0].chunks[0].matches) == 1
    assert len(docs[0].matches[0].matches) == 1
    assert len(docs[0].matches[0].matches[0].chunks) == 1


def test_selection():
    docs = apply_traversal_path(['cmm', 'mcm'])
    assert docs[0].chunks[0].matches[0].matches[0].granularity == 1
    assert docs[0].chunks[0].matches[0].matches[0].adjacency == 2
    assert len(docs[0].chunks[0].matches[0].matches) == 1
    assert docs[0].matches[0].chunks[0].matches[0].granularity == 1
    assert docs[0].matches[0].chunks[0].matches[0].adjacency == 2
    assert len(docs[0].matches[0].chunks[0].matches) == 1


def test_root_chunk():
    docs = apply_traversal_path(['r', 'c'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 2
    assert len(docs[0].chunks[0].chunks) == 2
    assert len(docs[0].chunks[1].chunks) == 1


def test_chunk_root():
    docs = apply_traversal_path(['c', 'r'])
    assert len(docs) == 1
    assert len(docs[0].chunks) == 2
    assert len(docs[0].chunks[0].chunks) == 2
    assert len(docs[0].chunks[1].chunks) == 0


def test_traverse_apply():
    docs = build_docs()
    doc = docs[0]
    doc.ClearField('chunks')
    docs = [doc, ]
    driver = AppendOneChunkTwoMatchesCrafter(traversal_paths=('mcm',))
    assert docs[0].matches[0].chunks[0].matches[0].granularity == 1
    assert docs[0].matches[0].chunks[0].matches[0].adjacency == 2
    driver._traverse_apply(docs)
    assert len(docs[0].matches[0].chunks[0].matches) == 1
    assert len(docs[0].matches[0].chunks[0].matches[0].chunks) == 2
    assert len(docs[0].matches[0].chunks[0].matches[0].matches) == 2
