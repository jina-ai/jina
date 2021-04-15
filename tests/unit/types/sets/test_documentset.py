from copy import deepcopy

import pytest
import numpy as np
from scipy.sparse import coo_matrix

from jina import Document
from jina.types.sets import DocumentSet

DOCUMENTS_PER_LEVEL = 1


@pytest.fixture(scope='function')
def document_factory():
    class DocumentFactory(object):
        def create(self, idx, text):
            with Document(id=idx) as d:
                d.tags['id'] = idx
                d.text = text
            return d

    return DocumentFactory()


@pytest.fixture
def docs(document_factory):
    return [
        document_factory.create(1, 'test 1'),
        document_factory.create(2, 'test 1'),
        document_factory.create(3, 'test 3'),
    ]


@pytest.fixture
def docset(docs):
    return DocumentSet(docs)


@pytest.fixture
def docset_with_scipy_sparse_embedding(docs):
    embedding = coo_matrix(
        (
            np.array([1, 2, 3, 4, 5, 6]),
            (np.array([0, 0, 1, 2, 2, 2]), np.array([0, 2, 2, 0, 1, 2])),
        ),
        shape=(4, 10),
    )
    for doc in docs:
        doc.embedding = embedding
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


def test_union(docset, document_factory):
    additional_docset = DocumentSet([])
    for idx in range(4, 10):
        doc = document_factory.create(idx, f'test {idx}')
        additional_docset.add(doc)
    union = docset + additional_docset
    for idx in range(0, 3):
        assert union[idx].id == docset[idx].id
    for idx in range(0, 6):
        assert union[idx + 3].id == additional_docset[idx].id


def test_union_inplace(docset, document_factory):
    additional_docset = DocumentSet([])
    for idx in range(4, 10):
        doc = document_factory.create(idx, f'test {idx}')
        additional_docset.add(doc)
    union = deepcopy(docset)
    union += additional_docset
    for idx in range(0, 3):
        assert union[idx].id == docset[idx].id
    for idx in range(0, 6):
        assert union[idx + 3].id == additional_docset[idx].id


def test_extend(docset, document_factory):
    docs = [document_factory.create(4, 'test 4'), document_factory.create(5, 'test 5')]
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
    doc_id = 2
    docset[doc_id] = doc
    assert docset[doc_id].text == 'test 4'
    doc_0_id = docset[0].id
    docset[doc_0_id] = doc
    assert docset[doc_0_id].text == 'test 4'


def test_set_get_from_slice_success(docs, document_factory):
    docset = DocumentSet(docs)
    assert len(docset[:1]) == 1
    assert len(docset[:2]) == 2
    assert len(docset[:3]) == 3
    assert len(docset[:100]) == 3

    assert len(docset[1:]) == 2
    assert len(docset[2:]) == 1
    assert len(docset[3:]) == 0
    assert len(docset[100:]) == 0


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


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('num_rows', [1, 2, 3])
@pytest.mark.parametrize('field', ['content', 'blob', 'embedding'])
def test_get_content(stack, num_rows, field):
    batch_size = 10
    embed_size = 20

    kwargs = {field: np.random.random((num_rows, embed_size))}

    docs = DocumentSet([Document(**kwargs) for _ in range(batch_size)])
    docs.append(Document())

    contents, pts = docs.extract_docs(field, stack_contents=stack)
    if stack:
        assert isinstance(contents, np.ndarray)
        assert contents.shape == (batch_size, num_rows, embed_size)
    else:
        assert len(contents) == batch_size
        for content in contents:
            assert content.shape == (num_rows, embed_size)


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('field', ['id', 'text'])
def test_get_content_text_fields(stack, field):
    batch_size = 10

    kwargs = {field: 'text'}

    docs = DocumentSet([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(field, stack_contents=stack)
    if stack:
        assert isinstance(contents, np.ndarray)
        assert contents.shape == (batch_size,)
    assert len(contents) == batch_size
    for content in contents:
        assert content == 'text'


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('bytes_input', [b'bytes', np.array([0, 0, 0]).tobytes()])
@pytest.mark.parametrize('field', ['content', 'buffer'])
def test_get_content_bytes_fields(stack, bytes_input, field):
    batch_size = 10

    kwargs = {field: bytes_input}

    docs = DocumentSet([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(field, stack_contents=stack)

    assert len(contents) == batch_size
    assert isinstance(contents, list)
    for content in contents:
        assert isinstance(content, bytes)
        assert content == bytes_input


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('fields', [['id', 'text'], ['content_hash', 'modality']])
def test_get_content_multiple_fields_text(stack, fields):
    batch_size = 10

    kwargs = {field: f'text-{field}' for field in fields}

    docs = DocumentSet([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(*fields, stack_contents=stack)

    assert len(contents) == len(fields)
    assert isinstance(contents, list)
    if stack:
        assert isinstance(contents[0], np.ndarray)
        assert isinstance(contents[1], np.ndarray)

    for content in contents:
        assert len(content) == batch_size
        if stack:
            assert content.shape == (batch_size,)


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('bytes_input', [b'bytes', np.array([0, 0, 0]).tobytes()])
def test_get_content_multiple_fields_text_buffer(stack, bytes_input):
    batch_size = 10
    fields = ['id', 'buffer']
    kwargs = {'id': 'text', 'buffer': bytes_input}

    docs = DocumentSet([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(*fields, stack_contents=stack)

    assert len(contents) == len(fields)
    assert isinstance(contents, list)
    assert len(contents[0]) == batch_size
    if stack:
        assert isinstance(contents[0], np.ndarray)
        assert contents[0].shape == (batch_size,)
    assert isinstance(contents[1], list)
    assert isinstance(contents[1][0], bytes)

    for content in contents:
        assert len(content) == batch_size


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('num_rows', [1, 2, 3])
def test_get_content_multiple_fields_arrays(stack, num_rows):
    fields = ['blob', 'embedding']

    batch_size = 10
    embed_size = 20

    kwargs = {field: np.random.random((num_rows, embed_size)) for field in fields}
    docs = DocumentSet([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(*fields, stack_contents=stack)

    assert len(contents) == len(fields)
    assert isinstance(contents, list)
    if stack:
        assert isinstance(contents[0], np.ndarray)
        assert isinstance(contents[1], np.ndarray)

    for content in contents:
        assert len(content) == batch_size
        if stack:
            assert content.shape == (batch_size, num_rows, embed_size)
        else:
            for c in content:
                assert c.shape == (num_rows, embed_size)


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('num_rows', [1, 2, 3])
def test_get_content_multiple_fields_merge(stack, num_rows):
    fields = ['embedding', 'text']

    batch_size = 10
    embed_size = 20

    kwargs = {
        field: np.random.random((num_rows, embed_size))
        if field == 'embedding'
        else 'text'
        for field in fields
    }
    docs = DocumentSet([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(*fields, stack_contents=stack)

    assert len(contents) == len(fields)
    assert isinstance(contents, list)
    if stack:
        assert isinstance(contents[0], np.ndarray)
        assert isinstance(contents[1], np.ndarray)

    for content in contents:
        assert len(content) == batch_size

    if stack:
        assert contents[0].shape == (batch_size, num_rows, embed_size)
        assert contents[1].shape == (batch_size,)
    else:
        assert len(contents[0]) == batch_size
        assert len(contents[1]) == batch_size
        for c in contents[0]:
            assert c.shape == (num_rows, embed_size)


def test_all_embeddings(docset_with_scipy_sparse_embedding):
    all_embeddings, doc_pts = docset_with_scipy_sparse_embedding.all_sparse_embeddings
    assert all_embeddings is not None
    assert doc_pts is not None
    assert len(doc_pts) == 3
    assert isinstance(all_embeddings, coo_matrix)
