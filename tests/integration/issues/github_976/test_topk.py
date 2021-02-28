import os

import numpy as np
import pytest

from jina import QueryLang
from jina.flow import Flow
from jina.proto import jina_pb2
from jina.types.ndarray.generic import NdArray

from tests import validate_callback


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_TOPK_DIR'] = str(tmpdir)
    os.environ['JINA_TOPK'] = '9'
    yield
    del os.environ['JINA_TOPK_DIR']
    del os.environ['JINA_TOPK']


def random_docs(num_docs, embed_dim=10, jitter=1):
    for j in range(num_docs):
        d = jina_pb2.DocumentProto()
        d.tags['id'] = j
        d.text = b'hello'
        NdArray(d.embedding).value = np.random.random([embed_dim + np.random.randint(0, jitter)])
        yield d


def test_topk(config, mocker):
    NDOCS = 3
    TOPK = int(os.getenv('JINA_TOPK'))

    def validate(resp):
        assert len(resp.search.docs) == NDOCS
        for doc in resp.search.docs:
            assert len(doc.matches) == TOPK

    with Flow.load_config('flow.yml') as index_flow:
        index_flow.index(inputs=random_docs(100))

    mock = mocker.Mock()
    with Flow.load_config('flow.yml') as search_flow:
        search_flow.search(inputs=random_docs(NDOCS),
                           on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate)


def test_topk_override(config, mocker):
    NDOCS = 3
    TOPK_OVERRIDE = 11

    def validate(resp):
        assert len(resp.search.docs) == NDOCS
        for doc in resp.search.docs:
            assert len(doc.matches) == TOPK_OVERRIDE

    # Making queryset
    top_k_queryset = QueryLang({'name': 'VectorSearchDriver', 'parameters': {'top_k': TOPK_OVERRIDE}, 'priority': 1})

    with Flow.load_config('flow.yml') as index_flow:
        index_flow.index(inputs=random_docs(100))

    mock = mocker.Mock()
    with Flow.load_config('flow.yml') as search_flow:
        search_flow.search(inputs=random_docs(NDOCS),
                           on_done=mock, queryset=[top_k_queryset])
    mock.assert_called_once()
    validate_callback(mock, validate)
