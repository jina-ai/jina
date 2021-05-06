from copy import deepcopy

import numpy as np
import pytest
import tensorflow as tf
import torch
from scipy.sparse import coo_matrix, csr_matrix

from jina import Document
from jina.enums import EmbeddingClsType
from jina.types.arrays import DocumentArray

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
def docarray(docs):
    return DocumentArray(docs)


@pytest.fixture
def docarray_with_scipy_sparse_embedding(docs):
    embedding = coo_matrix(
        (
            np.array([1, 2, 3, 4, 5, 6]),
            (np.array([0, 0, 0, 0, 0, 0]), np.array([0, 2, 2, 0, 1, 2])),
        ),
        shape=(1, 10),
    )
    for doc in docs:
        doc.embedding = embedding
    return DocumentArray(docs)


def test_length(docarray, docs):
    assert len(docs) == len(docarray) == 3


def test_append(docarray, document_factory):
    doc = document_factory.create(4, 'test 4')
    docarray.append(doc)
    assert docarray[-1].id == doc.id


def test_add(docarray, document_factory):
    doc = document_factory.create(4, 'test 4')
    docarray.add(doc)
    assert docarray[-1].id == doc.id


def test_union(docarray, document_factory):
    additional_docarray = DocumentArray([])
    for idx in range(4, 10):
        doc = document_factory.create(idx, f'test {idx}')
        additional_docarray.add(doc)
    union = docarray + additional_docarray
    for idx in range(0, 3):
        assert union[idx].id == docarray[idx].id
    for idx in range(0, 6):
        assert union[idx + 3].id == additional_docarray[idx].id


def test_union_inplace(docarray, document_factory):
    additional_docarray = DocumentArray([])
    for idx in range(4, 10):
        doc = document_factory.create(idx, f'test {idx}')
        additional_docarray.add(doc)
    union = deepcopy(docarray)
    union += additional_docarray
    for idx in range(0, 3):
        assert union[idx].id == docarray[idx].id
    for idx in range(0, 6):
        assert union[idx + 3].id == additional_docarray[idx].id


def test_extend(docarray, document_factory):
    docs = [document_factory.create(4, 'test 4'), document_factory.create(5, 'test 5')]
    docarray.extend(docs)
    assert len(docarray) == 5
    assert docarray[-1].tags['id'] == 5
    assert docarray[-1].text == 'test 5'


def test_clear(docarray):
    docarray.clear()
    assert len(docarray) == 0


def test_delete(docarray, document_factory):
    doc = document_factory.create(4, 'test 4')
    docarray.append(doc)
    del docarray[-1]
    assert len(docarray) == 3
    assert docarray == docarray


def test_build(docarray):
    docarray.build()


def test_array_get_success(docarray, document_factory):
    docarray.build()
    doc = document_factory.create(4, 'test 4')
    doc_id = 2
    docarray[doc_id] = doc
    assert docarray[doc_id].text == 'test 4'
    doc_0_id = docarray[0].id
    docarray[doc_0_id] = doc
    assert docarray[doc_0_id].text == 'test 4'


def test_array_get_from_slice_success(docs, document_factory):
    docarray = DocumentArray(docs)
    assert len(docarray[:1]) == 1
    assert len(docarray[:2]) == 2
    assert len(docarray[:3]) == 3
    assert len(docarray[:100]) == 3

    assert len(docarray[1:]) == 2
    assert len(docarray[2:]) == 1
    assert len(docarray[3:]) == 0
    assert len(docarray[100:]) == 0


def test_array_get_fail(docarray, document_factory):
    docarray.build()
    with pytest.raises(IndexError):
        docarray[0.1] = 1  # Set fail, not a supported type
    with pytest.raises(IndexError):
        docarray[0.1]  # Get fail, not a supported type


def test_docarray_init(docs, docarray):
    # we need low-level protobuf generation for testing
    assert len(docs) == len(docarray)
    for d, od in zip(docs, docarray):
        assert isinstance(d, Document)
        assert d.id == od.id
        assert d.text == od.text


def test_docarray_iterate_twice(docarray):
    j = 0
    for _ in docarray:
        for _ in docarray:
            j += 1
    assert j == len(docarray) ** 2


def test_docarray_reverse(docs, docarray):
    ids = [d.id for d in docs]
    docarray.reverse()
    ids2 = [d.id for d in docarray]
    assert list(reversed(ids)) == ids2


def test_match_chunk_array():
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
def documentarray():
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
    return DocumentArray(docs)


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

    docs = DocumentArray([Document(**kwargs) for _ in range(batch_size)])
    docs.append(Document())

    contents, pts = docs.get_fields(field, stack_contents=stack)
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

    docs = DocumentArray([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.get_fields(field, stack_contents=stack)
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

    docs = DocumentArray([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.get_fields(field, stack_contents=stack)

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

    docs = DocumentArray([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.get_fields(*fields, stack_contents=stack)

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

    docs = DocumentArray([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.get_fields(*fields, stack_contents=stack)

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
    docs = DocumentArray([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.get_fields(*fields, stack_contents=stack)

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
    docs = DocumentArray([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.get_fields(*fields, stack_contents=stack)

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


@pytest.mark.parametrize(
    'embedding_cls_type, return_expected_type',
    [
        (EmbeddingClsType.SCIPY_COO, coo_matrix),
        (EmbeddingClsType.SCIPY_CSR, csr_matrix),
        (EmbeddingClsType.TORCH, torch.Tensor),
        (EmbeddingClsType.TF, tf.SparseTensor),
    ],
)
def test_all_sparse_embeddings(
    docarray_with_scipy_sparse_embedding,
    embedding_cls_type,
    return_expected_type,
):
    (
        all_embeddings,
        doc_pts,
    ) = docarray_with_scipy_sparse_embedding.get_all_sparse_embeddings(
        embedding_cls_type=embedding_cls_type,
    )
    assert all_embeddings is not None
    assert doc_pts is not None
    assert len(doc_pts) == 3

    if embedding_cls_type.is_scipy:
        assert isinstance(all_embeddings, return_expected_type)
        assert all_embeddings.shape == (3, 10)
    if embedding_cls_type.is_torch:
        assert isinstance(all_embeddings, return_expected_type)
        assert all_embeddings.is_sparse
        assert all_embeddings.shape[0] == 3
        assert all_embeddings.shape[1] == 10
    if embedding_cls_type.is_tf:
        assert isinstance(all_embeddings, list)
        assert isinstance(all_embeddings[0], return_expected_type)
        assert len(all_embeddings) == 3
        assert all_embeddings[0].shape[0] == 1
        assert all_embeddings[0].shape[1] == 10
