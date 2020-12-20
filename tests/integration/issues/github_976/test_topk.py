import os

import numpy as np
import pytest

from jina import QueryLang
from jina.drivers.search import VectorSearchDriver
from jina.flow import Flow
from jina.proto import jina_pb2
from jina.types.ndarray.generic import NdArray


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

    def validate_results(resp):
        assert len(resp.search.docs) == NDOCS
        for doc in resp.search.docs:
            assert len(doc.matches) == TOPK

    response_mock = mocker.Mock(wraps=validate_results)

    with Flow.load_config('flow.yml') as index_flow:
        index_flow.index(input_fn=random_docs(100))

    with Flow.load_config('flow.yml') as search_flow:
        search_flow.search(input_fn=random_docs(NDOCS),
                           on_done=response_mock)

    response_mock.assert_called()


def test_topk_override(config, mocker):
    NDOCS = 3
    TOPK_OVERRIDE = 11

    def validate_override_results(resp):
        assert len(resp.search.docs) == NDOCS
        for doc in resp.search.docs:
            assert len(doc.matches) == TOPK_OVERRIDE

    response_mock = mocker.Mock(wraps=validate_override_results)

    # Making queryset
    top_k_queryset = QueryLang(VectorSearchDriver(top_k=TOPK_OVERRIDE, priority=1))

    with Flow.load_config('flow.yml') as index_flow:
        index_flow.index(input_fn=random_docs(100))

    with Flow.load_config('flow.yml') as search_flow:
        search_flow.search(input_fn=random_docs(NDOCS),
                           on_done=response_mock, queryset=[top_k_queryset])

    response_mock.assert_called()
