import os
import shutil

import numpy as np
import pytest

from jina.flow import Flow
from jina import Document


@pytest.fixture
def parallel(request):
    os.environ['JINA_TEST_REF_INDEXER_PARALLEL'] = str(request.param)
    yield
    del os.environ['JINA_TEST_REF_INDEXER_PARALLEL']


@pytest.fixture
def index_docs():
    docs = []
    for idx in range(0, 100):
        doc = Document()
        doc.id = f'{idx:0>16}'
        doc.embedding = doc.embedding = np.array([idx, idx])
        docs.append(doc)
    return docs


@pytest.fixture
def random_workspace(tmpdir):
    os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER'] = str(tmpdir)
    os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER_QUERY'] = str(tmpdir)
    yield
    del os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER']
    del os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER_QUERY']


@pytest.mark.parametrize('parallel', [1, 2], indirect=True)
def test_indexer_with_ref_indexer(random_workspace, parallel, index_docs, mocker):
    top_k = 10
    with Flow.load_config('index.yml') as index_flow:
        index_flow.index(input_fn=index_docs, batch_size=10)

    mock = mocker.Mock()

    def validate_response(resp):
        mock()
        assert len(resp.search.docs) == 1
        assert len(resp.search.docs[0].matches) == top_k

    query_document = Document()
    query_document.embedding = np.array([1, 1])
    with Flow.load_config('query.yml') as query_flow:
        query_flow.search(input_fn=[query_document], on_done=validate_response, top_k=top_k)

    mock.assert_called_once()


@pytest.fixture
def random_workspace_move(tmpdir):
    os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER'] = str(tmpdir) + '/index'
    os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER_QUERY'] = str(tmpdir) + '/query'
    yield
    del os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER']
    del os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER_QUERY']


@pytest.mark.parametrize('parallel', [1, 2], indirect=True)
def test_indexer_with_ref_indexer_move(random_workspace_move, parallel, index_docs, mocker):
    top_k = 10
    with Flow.load_config('index.yml') as index_flow:
        index_flow.index(input_fn=index_docs, batch_size=10)

    mock = mocker.Mock()

    shutil.copytree(os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER'],
                    os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER_QUERY'])

    shutil.rmtree(os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER'])

    def validate_response(resp):
        mock()
        assert len(resp.search.docs) == 1
        assert len(resp.search.docs[0].matches) == top_k

    query_document = Document()
    query_document.embedding = np.array([1, 1])
    with Flow.load_config('query.yml') as query_flow:
        query_flow.search(input_fn=[query_document], on_done=validate_response, top_k=top_k)

    mock.assert_called_once()
