from copy import deepcopy

import numpy as np
import pytest
from scipy.sparse import coo_matrix

from jina import Document, DocumentArray

DOCUMENTS_PER_LEVEL = 1


@pytest.fixture
def docarray_for_cache():
    da = DocumentArray()
    d1 = Document(id=1)
    d2 = Document(id='2')
    da.extend([d1, d2])
    return da


@pytest.fixture(scope='function')
def document_factory():
    class DocumentFactory(object):
        def create(self, idx, text):
            return Document(id=idx, tags={'id': idx}, text=text)

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
    d = Document(content='hello world')

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
    chunk = Document()
    chunk.granularity = doc.granularity + 1
    chunk.adjacency = doc.adjacency
    doc.chunks.append(chunk)
    return chunk


def add_match(doc):
    match = Document()
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


def test_da_sort_topk():
    da = DocumentArray([Document(id=i, scores={'euclid': 10 - i}) for i in range(10)])
    original = deepcopy(da)

    da.sort(top_k=3, key=lambda d: d.scores['euclid'].value)
    top = [da[i].scores['euclid'].value for i in range(3)]
    rest = [da[i].scores['euclid'].value for i in range(3, 10)]
    assert top[0] == 1 and top[1] == 2 and top[2] == 3
    assert rest != sorted(rest)
    assert len(da) == len(original)
    assert all([d.id in original for d in da])

    da.sort(top_k=3, key=lambda d: d.scores['euclid'].value, reverse=True)
    top = [da[i].scores['euclid'].value for i in range(3)]
    rest = [da[i].scores['euclid'].value for i in range(3, 10)]
    assert top[0] == 10 and top[1] == 9 and top[2] == 8
    assert rest != sorted(rest, reverse=True)
    assert len(da) == len(original)
    assert all([d.id in original for d in da])


def test_da_sort_topk_tie():
    da = DocumentArray([Document(id=i, tags={'order': i % 10}) for i in range(100)])
    da.sort(top_k=10, key=lambda doc: doc.tags['order'])

    top_k_ids = [doc.id for doc in da[0:10]]
    assert top_k_ids == ['0', '10', '20', '30', '40', '50', '60', '70', '80', '90']
    for i in range(10):
        assert da[i].tags['order'] == 0


def test_da_reverse():
    docs = [Document(embedding=np.array([1] * (10 - i))) for i in range(10)]
    da = DocumentArray(
        [docs[i] if (i % 2 == 0) else docs[i].proto for i in range(len(docs))]
    )
    assert len(da) == 10
    assert da[0].embedding.shape == (10,)
    da0_id = da[0].id
    da.reverse()
    assert da[0].id != da0_id
    assert da[da0_id].id == da0_id
    assert da[-1].id == da0_id
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


def test_cache_invalidation_clear(docarray_for_cache):
    assert '1' in docarray_for_cache
    assert '2' in docarray_for_cache
    docarray_for_cache.clear()
    assert '1' not in docarray_for_cache
    assert '2' not in docarray_for_cache


def test_cache_invalidation_insert(docarray_for_cache):
    """Test insert doc at certain idx."""
    docarray_for_cache.insert(0, Document(id='test_id'))
    assert 'test_id' in docarray_for_cache
    assert docarray_for_cache[0].id == 'test_id'


def test_cache_invalidation_set_del(docarray_for_cache):
    docarray_for_cache[0] = Document(id='test_id')
    docarray_for_cache[1] = Document(id='test_id2')
    assert 'test_id' in docarray_for_cache
    assert 'test_id2' in docarray_for_cache
    del docarray_for_cache['test_id']
    assert 'test_id' not in docarray_for_cache


def test_cache_invalidation_sort_reverse(docarray_for_cache):
    assert docarray_for_cache[0].id == '1'
    assert docarray_for_cache[1].id == '2'
    docarray_for_cache.reverse()
    assert docarray_for_cache[0].id == '2'
    assert docarray_for_cache[1].id == '1'


def test_none_extend():
    da = DocumentArray([Document() for _ in range(100)])
    da.extend(None)
    assert len(da) == 100


def test_lazy_index_map():
    da = DocumentArray([Document(id=str(i), text=f'document_{i}') for i in range(100)])
    assert da._id_to_index is None

    # build index map
    assert da['0'].text == 'document_0'
    assert da._id_to_index is not None
    assert len(da._index_map.keys()) == 100
