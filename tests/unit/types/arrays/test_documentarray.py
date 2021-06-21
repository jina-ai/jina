import os
from copy import deepcopy

import pytest

import numpy as np
from scipy.sparse import coo_matrix

from jina import Document, DocumentArray
from jina.logging.profile import TimeContext
from jina.types.document.graph import GraphDocument
from tests import random_docs

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


def test_union(docarray, document_factory):
    additional_docarray = DocumentArray([])
    for idx in range(4, 10):
        doc = document_factory.create(idx, f'test {idx}')
        additional_docarray.append(doc)
    union = docarray + additional_docarray
    for idx in range(0, 3):
        assert union[idx].id == docarray[idx].id
    for idx in range(0, 6):
        assert union[idx + 3].id == additional_docarray[idx].id


def test_union_inplace(docarray, document_factory):
    additional_docarray = DocumentArray([])
    for idx in range(4, 10):
        doc = document_factory.create(idx, f'test {idx}')
        additional_docarray.append(doc)
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


def test_delete_by_index(docarray, document_factory):
    doc = document_factory.create(4, 'test 4')
    docarray.append(doc)
    del docarray[-1]
    assert len(docarray) == 3
    assert docarray == docarray


def test_delete_by_id(docarray: DocumentArray, document_factory):
    doc = document_factory.create(4, 'test 4')
    docarray.append(doc)
    del docarray[doc.id]
    assert len(docarray) == 3
    assert docarray == docarray


def test_array_get_success(docarray, document_factory):
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

    m = Document()
    d.matches.append(m)
    assert m.granularity == d.granularity
    assert m.adjacency == 0
    assert d.matches[0].adjacency == d.adjacency + 1
    assert len(d.matches) == 1

    c = Document()
    d.chunks.append(c)
    assert c.granularity == 0
    assert d.chunks[0].granularity == d.granularity + 1
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
        doc.matches.append(match)
        return match


def test_doc_array_from_generator():
    NUM_DOCS = 100

    def generate():
        for _ in range(NUM_DOCS):
            yield Document()

    doc_array = DocumentArray(generate())
    assert len(doc_array) == NUM_DOCS


@pytest.mark.parametrize('method', ['json', 'binary'])
def test_document_save_load(method, tmp_path):
    da1 = DocumentArray(random_docs(1000))
    da2 = DocumentArray()
    for doc in random_docs(10):
        da2.append(doc)
    for da in [da1, da2]:
        tmp_file = os.path.join(tmp_path, 'test')
        with TimeContext(f'w/{method}'):
            da.save(tmp_file, file_format=method)
        with TimeContext(f'r/{method}'):
            da_r = DocumentArray.load(tmp_file, file_format=method)
        assert len(da) == len(da_r)
        for d, d_r in zip(da, da_r):
            assert d.id == d_r.id
            np.testing.assert_equal(d.embedding, d_r.embedding)
            assert d.content == d_r.content


def test_documentarray_filter():
    da = DocumentArray([Document() for _ in range(6)])

    for j in range(6):
        da[j].scores['score'].value = j

    da = [d for d in da if d.scores['score'].value > 2]
    assert len(DocumentArray(da)) == 3

    for d in da:
        assert d.scores['score'].value > 2


def test_da_with_different_inputs():
    docs = [Document() for _ in range(10)]
    da = DocumentArray(
        [docs[i] if (i % 2 == 0) else docs[i].proto for i in range(len(docs))]
    )
    assert len(da) == 10
    for d in da:
        assert isinstance(d, Document)


def test_da_sort_by_document_interface_not_in_proto():
    docs = [Document(embedding=np.array([1] * (10 - i))) for i in range(10)]
    da = DocumentArray(
        [docs[i] if (i % 2 == 0) else docs[i].proto for i in range(len(docs))]
    )
    assert len(da) == 10
    assert da[0].embedding.shape == (10,)

    da.sort(key=lambda d: d.embedding.shape[0])
    assert da[0].embedding.shape == (1,)


def test_da_sort_by_document_interface_in_proto():
    docs = [Document(embedding=np.array([1] * (10 - i))) for i in range(10)]
    da = DocumentArray(
        [docs[i] if (i % 2 == 0) else docs[i].proto for i in range(len(docs))]
    )
    assert len(da) == 10
    assert da[0].embedding.shape == (10,)

    da.sort(key=lambda d: d.embedding.dense.shape[0])
    assert da[0].embedding.shape == (1,)


def test_da_reverse():
    docs = [Document(embedding=np.array([1] * (10 - i))) for i in range(10)]
    da = DocumentArray(
        [docs[i] if (i % 2 == 0) else docs[i].proto for i in range(len(docs))]
    )
    assert len(da) == 10
    assert da[0].embedding.shape == (10,)
    da.reverse()
    assert da[0].embedding.shape == (1,)


def test_da_sort_by_score():
    da = DocumentArray(
        [Document(id=i, copy=True, scores={'euclid': 10 - i}) for i in range(10)]
    )
    assert da[0].id == '0'
    assert da[0].scores['euclid'].value == 10
    da.sort(key=lambda d: d.scores['euclid'].value)  # sort matches by their values
    assert da[0].id == '9'
    assert da[0].scores['euclid'].value == 1


def test_da_sort_by_score():
    da = DocumentArray(
        [Document(id=i, copy=True, scores={'euclid': 10 - i}) for i in range(10)]
    )
    assert da[0].id == '0'
    assert da[0].scores['euclid'].value == 10
    da.sort(key=lambda d: d.scores['euclid'].value)  # sort matches by their values
    assert da[0].id == '9'
    assert da[0].scores['euclid'].value == 1
