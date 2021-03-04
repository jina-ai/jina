from jina.drivers import FlatRecursiveMixin, BaseExecutableDriver
from jina import DocumentSet, Document

DOCUMENTS_PER_LEVEL = 1


class AppendOneChunkTwoMatchesCrafter(FlatRecursiveMixin, BaseExecutableDriver):
    def __init__(self, docs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = docs

    @property
    def docs(self):
        return self._docs

    def _apply_all(self, docs, *args, **kwargs) -> None:
        for doc in docs:
            add_chunk(doc)
            add_match(doc)
            add_match(doc)


def add_chunk(doc):
    chunk = Document()
    chunk.granularity = doc.granularity + 1
    chunk.adjacency = doc.adjacency
    return doc.chunks.add(chunk)


def add_match(doc):
    match = Document()
    match.granularity = doc.granularity
    match.adjacency = doc.adjacency + 1
    return doc.matches.add(match)


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
        document = Document()
        document.granularity = 0
        document.adjacency = 0
        docs.append(document)
        iterate_build(document, 0, 0)
    return DocumentSet(docs)


def apply_traversal_path(traversal_paths):
    docs = build_docs()
    driver = AppendOneChunkTwoMatchesCrafter(docs=docs, traversal_paths=traversal_paths)
    driver()
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


def test_call():
    docs = build_docs()
    doc = docs[0]
    doc.ClearField('chunks')
    docs = DocumentSet([doc])
    driver = AppendOneChunkTwoMatchesCrafter(docs=docs, traversal_paths=('mcm',))
    assert docs[0].matches[0].chunks[0].matches[0].granularity == 1
    assert docs[0].matches[0].chunks[0].matches[0].adjacency == 2
    driver()
    assert len(docs[0].matches[0].chunks[0].matches) == 1
    assert len(docs[0].matches[0].chunks[0].matches[0].chunks) == 2
    assert len(docs[0].matches[0].chunks[0].matches[0].matches) == 2
