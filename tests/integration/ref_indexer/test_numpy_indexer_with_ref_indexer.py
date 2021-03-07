import os
import shutil

import numpy as np
import pytest

from jina.flow import Flow
from jina import Document

from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def uses_no_docker():
    os.environ['JINA_QUERY_USES'] = 'indexer_with_ref.yml'
    os.environ['JINA_QUERY_USES_INTERNAL'] = ''
    os.environ['JINA_QUERY_USES_COMPOUND'] = 'compound-indexer-with-ref.yml'
    os.environ['JINA_QUERY_USES_COMPOUND_INTERNAL'] = ''
    yield
    del os.environ['JINA_QUERY_USES']
    del os.environ['JINA_QUERY_USES_COMPOUND']
    del os.environ['JINA_QUERY_USES_INTERNAL']
    del os.environ['JINA_QUERY_USES_COMPOUND_INTERNAL']


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
def test_indexer_with_ref_indexer(
    random_workspace, parallel, index_docs, mocker, uses_no_docker
):
    top_k = 10
    with Flow.load_config(os.path.join('index.yml')) as index_flow:
        index_flow.index(inputs=index_docs, request_size=10)

    mock = mocker.Mock()

    def validate_response(resp):
        assert len(resp.search.docs) == 1
        assert len(resp.search.docs[0].matches) == top_k

    query_document = Document()
    query_document.embedding = np.array([1, 1])
    with Flow.load_config(os.path.join('query.yml')) as query_flow:
        query_flow.search(inputs=[query_document], on_done=mock, top_k=top_k)

    mock.assert_called_once()
    validate_callback(mock, validate_response)


@pytest.mark.parametrize('parallel', [1, 2], indirect=True)
def test_indexer_with_ref_indexer_compound(
    random_workspace, parallel, index_docs, mocker, uses_no_docker
):
    top_k = 10
    with Flow.load_config(os.path.join(cur_dir, 'compound-index.yml')) as index_flow:
        index_flow.index(inputs=index_docs, request_size=10)

    mock = mocker.Mock()

    def validate_response(resp):
        assert len(resp.search.docs) == 1
        assert len(resp.search.docs[0].matches) == top_k

    query_document = Document()
    query_document.embedding = np.array([1, 1])
    with Flow.load_config(os.path.join(cur_dir, 'compound-query.yml')) as query_flow:
        query_flow.search(inputs=[query_document], on_done=mock, top_k=top_k)

    mock.assert_called_once()
    validate_callback(mock, validate_response)


@pytest.fixture
def random_workspace_move(tmpdir):
    os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER'] = str(tmpdir) + '/index'
    os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER_QUERY'] = str(tmpdir) + '/query'
    yield
    del os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER']
    del os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER_QUERY']


@pytest.mark.parametrize('parallel', [1, 2], indirect=True)
def test_indexer_with_ref_indexer_move(
    random_workspace_move, parallel, index_docs, mocker, uses_no_docker
):
    top_k = 10
    with Flow.load_config(os.path.join(cur_dir, 'index.yml')) as index_flow:
        index_flow.index(inputs=index_docs, request_size=10)

    mock = mocker.Mock()

    shutil.copytree(
        os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER'],
        os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER_QUERY'],
    )

    shutil.rmtree(os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER'])

    def validate_response(resp):
        assert len(resp.search.docs) == 1
        assert len(resp.search.docs[0].matches) == top_k

    query_document = Document()
    query_document.embedding = np.array([1, 1])
    with Flow.load_config(os.path.join(cur_dir, 'query.yml')) as query_flow:
        query_flow.search(inputs=[query_document], on_done=mock, top_k=top_k)

    mock.assert_called_once()
    validate_callback(mock, validate_response)


@pytest.mark.parametrize('parallel', [1, 2], indirect=True)
def test_indexer_with_ref_indexer_compound_move(
    random_workspace_move, parallel, index_docs, mocker, uses_no_docker
):
    top_k = 10
    with Flow.load_config(os.path.join(cur_dir, 'compound-index.yml')) as index_flow:
        index_flow.index(inputs=index_docs, request_size=10)

    mock = mocker.Mock()

    shutil.copytree(
        os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER'],
        os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER_QUERY'],
    )

    shutil.rmtree(os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER'])

    def validate_response(resp):
        assert len(resp.search.docs) == 1
        assert len(resp.search.docs[0].matches) == top_k

    query_document = Document()
    query_document.embedding = np.array([1, 1])
    with Flow.load_config(os.path.join(cur_dir, 'compound-query.yml')) as query_flow:
        query_flow.search(inputs=[query_document], on_done=mock, top_k=top_k)

    mock.assert_called_once()
    validate_callback(mock, validate_response)


@pytest.fixture
def docker_image():
    from jina.parsers.hub import set_hub_build_parser
    from jina.docker.hubio import HubIO

    args = set_hub_build_parser().parse_args([os.path.join(cur_dir, 'numpyhub')])
    HubIO(args).build()


@pytest.fixture
def uses_docker(docker_image):
    from jina import __version__ as jina_version

    os.environ[
        'JINA_QUERY_USES'
    ] = f'docker://jinahub/pod.indexer.dummynumpyindexer:0.0.0-{jina_version}'
    os.environ[
        'JINA_QUERY_USES_COMPOUND'
    ] = f'docker://jinahub/pod.indexer.dummynumpyindexer:0.0.0-{jina_version}'
    os.environ['JINA_QUERY_USES_INTERNAL'] = 'indexer_with_ref.yml'
    os.environ['JINA_QUERY_USES_COMPOUND_INTERNAL'] = 'compound-indexer-with-ref.yml'
    yield
    del os.environ['JINA_QUERY_USES']
    del os.environ['JINA_QUERY_USES_COMPOUND']


@pytest.fixture
def random_workspace_in_docker(tmpdir):
    os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER'] = str(tmpdir)
    os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER_QUERY'] = '/docker-workspace'
    os.environ['JINA_VOLUMES'] = f'{str(tmpdir)}:/docker-workspace'
    yield
    del os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER']
    del os.environ['JINA_TEST_INDEXER_WITH_REF_INDEXER_QUERY']
    del os.environ['JINA_VOLUMES']


@pytest.mark.parametrize('parallel', [1, 2], indirect=True)
def test_indexer_with_ref_indexer_in_docker(
    random_workspace_in_docker, parallel, index_docs, mocker, uses_docker
):
    top_k = 10
    with Flow.load_config(os.path.join('index.yml')) as index_flow:
        index_flow.index(inputs=index_docs, request_size=10)

    mock = mocker.Mock()

    def validate_response(resp):
        assert len(resp.search.docs) == 1
        assert len(resp.search.docs[0].matches) == top_k

    query_document = Document()
    query_document.embedding = np.array([1, 1])
    with Flow.load_config(os.path.join('query.yml')) as query_flow:
        query_flow.search(inputs=[query_document], on_done=mock, top_k=top_k)

    mock.assert_called_once()
    validate_callback(mock, validate_response)


@pytest.mark.parametrize('parallel', [1, 2], indirect=True)
def test_indexer_with_ref_indexer_compound_in_docker(
    random_workspace_in_docker, parallel, index_docs, mocker, uses_docker
):
    top_k = 10
    with Flow.load_config(os.path.join(cur_dir, 'compound-index.yml')) as index_flow:
        index_flow.index(inputs=index_docs, request_size=10)

    mock = mocker.Mock()

    def validate_response(resp):
        assert len(resp.search.docs) == 1
        assert len(resp.search.docs[0].matches) == top_k

    query_document = Document()
    query_document.embedding = np.array([1, 1])
    with Flow.load_config(os.path.join(cur_dir, 'compound-query.yml')) as query_flow:
        query_flow.search(inputs=[query_document], on_done=mock, top_k=top_k)

    mock.assert_called_once()
    validate_callback(mock, validate_response)
