import os
import time
from copy import deepcopy

import numpy as np
import pytest
from scipy.sparse import coo_matrix

from jina import Document, DocumentArrayRedis

DOCUMENTS_PER_LEVEL = 1


@pytest.fixture
def docarray_for_cache():
    da = DocumentArrayRedis(clear=True)
    d1 = Document(id=1)
    d2 = Document(id='2')
    da.extend([d1, d2])
    return da


@pytest.fixture()
def docker_compose(request):
    os.system(
        f'docker-compose -f {request.param} --project-directory . up  --build -d '
        f'--remove-orphans'
    )
    time.sleep(5)
    yield
    os.system(
        f'docker-compose -f {request.param} --project-directory . down '
        f'--remove-orphans'
    )


cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.abspath(os.path.join(cur_dir, 'docker-compose.yml'))


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
    docs_redis = DocumentArrayRedis(docs, clear=True)
    assert len(docs_redis) == 3
    return docs_redis


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
    return DocumentArrayRedis(docs)


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_length(docarray, docs, docker_compose):
    assert len(docs) == len(docarray) == 3


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_append(docarray, document_factory, docker_compose):
    doc = document_factory.create(4, 'test 4')
    docarray.append(doc)
    assert docarray[-1].id == doc.id


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_extend(docarray, document_factory, docker_compose):
    docs = [document_factory.create(4, 'test 4'), document_factory.create(5, 'test 5')]
    docarray.extend(docs)
    assert len(docarray) == 5
    assert docarray[-1].tags['id'] == 5
    assert docarray[-1].text == 'test 5'


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_clear(docarray, docker_compose):
    docarray.clear()
    assert len(docarray) == 0


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_delete_by_index(docarray, document_factory, docker_compose):
    doc = document_factory.create(4, 'test 4')
    docarray.append(doc)
    del docarray[-1]
    assert len(docarray) == 3
    assert docarray == docarray


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_delete_by_id(docarray: DocumentArrayRedis, document_factory, docker_compose):
    doc = document_factory.create(4, 'test 4')
    docarray.append(doc)
    del docarray[doc.id]
    assert len(docarray) == 3
    assert docarray == docarray


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_array_get_success(docarray, document_factory, docker_compose):
    doc = document_factory.create(4, 'test 4')
    doc_id = 2
    docarray[doc_id] = doc
    assert docarray[doc_id].text == 'test 4'
    doc_0_id = docarray[0].id
    docarray[doc_0_id] = doc
    assert docarray[doc_0_id].text == 'test 4'


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_array_get_from_slice_success(docs, document_factory, docker_compose):
    DocumentArrayRedis().clear()
    docarray = DocumentArrayRedis(docs)
    assert len(docarray[:1]) == 1
    assert len(docarray[:2]) == 2
    assert len(docarray[:3]) == 3
    assert len(docarray[:100]) == 3

    assert len(docarray[1:]) == 2
    assert len(docarray[2:]) == 1
    assert len(docarray[3:]) == 0
    assert len(docarray[100:]) == 0


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_array_get_fail(docarray, document_factory, docker_compose):
    with pytest.raises(IndexError):
        docarray[0.1] = 1  # Set fail, not a supported type
    with pytest.raises(IndexError):
        docarray[0.1]  # Get fail, not a supported type


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_docarray_init(docs, docarray, docker_compose):
    # we need low-level protobuf generation for testing
    assert len(docs) == len(docarray)
    for d, od in zip(docs, docarray):
        assert isinstance(d, Document)
        assert d.id == od.id
        assert d.text == od.text


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_docarray_iterate_twice(docarray, docker_compose):
    j = 0
    for _ in docarray:
        for _ in docarray:
            j += 1
    assert j == len(docarray) ** 2


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_match_chunk_array(docker_compose):
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


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_doc_array_from_generator(docker_compose):
    NUM_DOCS = 100

    def generate():
        for _ in range(NUM_DOCS):
            yield Document()

    doc_array = DocumentArrayRedis(generate(), clear=True)
    assert len(doc_array) == NUM_DOCS


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_documentarray_filter(docker_compose):
    da = DocumentArrayRedis([Document() for _ in range(6)], clear=True)

    for j in range(6):
        # no retrieving by reference
        d = da[j]
        d.scores['score'].value = j
        da[j] = d

    da2 = [d for d in da if d.scores['score'].value > 2]
    assert len(DocumentArrayRedis(da2, name='another', clear=True)) == 3

    for d in da2:
        assert d.scores['score'].value > 2


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_da_with_different_inputs(docker_compose):
    docs = [Document() for _ in range(10)]
    da = DocumentArrayRedis(
        [docs[i] if (i % 2 == 0) else docs[i].proto for i in range(len(docs))],
        clear=True,
    )
    assert len(da) == 10
    for d in da:
        assert isinstance(d, Document)


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_da_document_interface_not_in_proto(docker_compose):
    docs = [Document(embedding=np.array([1] * (10 - i))) for i in range(10)]
    da = DocumentArrayRedis(
        [docs[i] if (i % 2 == 0) else docs[i].proto for i in range(len(docs))],
        clear=True,
    )
    assert len(da) == 10
    assert da[0].embedding.shape == (10,)


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_cache_invalidation_clear(docarray_for_cache, docker_compose):
    assert '1' in docarray_for_cache
    assert '2' in docarray_for_cache
    docarray_for_cache.clear()
    assert '1' not in docarray_for_cache
    assert '2' not in docarray_for_cache


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_cache_invalidation_insert(docarray_for_cache, docker_compose):
    """Test insert doc at certain idx."""
    docarray_for_cache.insert(0, Document(id='test_id'))
    assert 'test_id' in docarray_for_cache
    assert docarray_for_cache[0].id == 'test_id'


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_cache_invalidation_set_del(docarray_for_cache, docker_compose):
    docarray_for_cache[0] = Document(id='test_id')
    docarray_for_cache[1] = Document(id='test_id2')
    assert 'test_id' in docarray_for_cache
    assert 'test_id2' in docarray_for_cache
    del docarray_for_cache['test_id']
    assert 'test_id' not in docarray_for_cache


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_none_extend(docker_compose):
    da = DocumentArrayRedis([Document() for _ in range(100)], clear=True)
    da.extend(None)
    assert len(da) == 100
