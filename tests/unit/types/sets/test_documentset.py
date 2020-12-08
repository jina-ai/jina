import pytest

from jina import Document
from jina.types.sets import DocumentSet

DOCUMENTS_PER_LEVEL = 1


@pytest.fixture(scope='function')
def document_factory():
    class DocumentFactory(object):
        def create(self, idx, text):
            with Document() as d:
                d.tags['id'] = idx
                d.text = text
            return d

    return DocumentFactory()


@pytest.fixture
def docs(document_factory):
    return [
        document_factory.create(1, 'test 1'),
        document_factory.create(2, 'test 1'),
        document_factory.create(3, 'test 3')
    ]


@pytest.fixture
def docset(docs):
    return DocumentSet(docs)


def test_length(docset, docs):
    assert len(docs) == len(docset) == 3


def test_append(docset, document_factory):
    doc = document_factory.create(4, 'test 4')
    docset.append(doc)
    assert docset[-1].id == doc.id


def test_add(docset, document_factory):
    doc = document_factory.create(4, 'test 4')
    docset.add(doc)
    assert docset[-1].id == doc.id


def test_extend(docset, document_factory):
    docs = [
        document_factory.create(4, 'test 4'),
        document_factory.create(5, 'test 5')
    ]
    docset.extend(docs)
    assert len(docset) == 5
    assert docset[-1].tags['id'] == 5
    assert docset[-1].text == 'test 5'


def test_clear(docset):
    docset.clear()
    assert len(docset) == 0


def test_delete(docset, document_factory):
    doc = document_factory.create(4, 'test 4')
    docset.append(doc)
    del docset[-1]
    assert len(docset) == 3
    assert docset == docset


def test_build(docset):
    docset.build()


def test_set_get_success(docset, document_factory):
    docset.build()
    doc = document_factory.create(4, 'test 4')
    docset[2] = doc
    assert docset[2].text == 'test 4'
    doc_0_id = docset[0].id
    docset[doc_0_id] = doc
    assert docset[doc_0_id].text == 'test 4'


def test_set_get_fail(docset, document_factory):
    docset.build()
    with pytest.raises(IndexError):
        docset[0.1] = 1  # Set fail, not a supported type
    with pytest.raises(IndexError):
        docset[0.1]  # Get fail, not a supported type


def test_docset_init(docs, docset):
    # we need low-level protobuf generation for testing
    assert len(docs) == len(docset)
    for d, od in zip(docs, docset):
        assert isinstance(d, Document)
        assert d.id == od.id
        assert d.text == od.text


def test_docset_iterate_twice(docset):
    j = 0
    for _ in docset:
        for _ in docset:
            j += 1
    assert j == len(docset) ** 2


def test_docset_reverse(docs, docset):
    ids = [d.id for d in docs]
    docset.reverse()
    ids2 = [d.id for d in docset]
    assert list(reversed(ids)) == ids2


def test_match_chunk_set():
    with Document() as d:
        d.content = 'hello world'

    m = d.matches.new()
    assert m.granularity == d.granularity
    assert m.adjacency == d.adjacency + 1
    assert len(d.matches) == 1

    c = d.chunks.new()
    assert c.granularity == d.granularity + 1
    assert c.adjacency == d.adjacency
    assert len(d.chunks) == 1


def add_chunk(doc):
    with Document() as chunk:
        chunk.granularity = doc.granularity + 1
        chunk.adjacency = doc.adjacency
        doc.chunks.append(chunk)
        return chunk


def add_match(doc):
    with Document() as match:
        match.granularity = doc.granularity
        match.adjacency = doc.adjacency + 1
        doc.matches.add(match)
        return match


@pytest.fixture
def documentset():
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
        with Document() as d:
            d.granularity = 0
            d.adjacency = 0
            docs.append(d)
            iterate_build(d, 0, 0)
    return DocumentSet(docs)


def callback_fn(docs, *args, **kwargs) -> None:
    for doc in docs:
        add_chunk(doc)
        add_match(doc)
        add_match(doc)
