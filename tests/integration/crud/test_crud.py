import os

import numpy as np
import pytest

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
        d.id = str(f'{j}'*16)
        d.text = b'hello'
        NdArray(d.embedding).value = np.random.random([embed_dim + np.random.randint(0, jitter)])
        yield d

def test_delete(config, mocker):
    NUMBER_OF_SEARCHES = 3
    def validate_results(resp):
        assert len(resp.search.docs) == NUMBER_OF_SEARCHES
        for doc in resp.search.docs:
            assert len(doc.matches) == 0

    response_mock = mocker.Mock(wraps=validate_results)
    docs = list(random_docs(10))
    for method in [
        'index',
        'delete'
    ]:
        with Flow.load_config('flow.yml') as index_flow:
            getattr(index_flow, method)(input_fn=(d for d in docs))
    with Flow.load_config('flow.yml') as search_flow:
        search_flow.search(input_fn=random_docs(NUMBER_OF_SEARCHES),
                           output_fn=response_mock)
    response_mock.assert_called()

def test_update(config, mocker):
    NUMBER_OF_SEARCHES = 3
    docs_before = list(random_docs(10))
    docs_updated = list(random_docs(10))
    def validate_results(resp):
        print('start validation')
        assert len(resp.search.docs) == NUMBER_OF_SEARCHES
        hash_set_before = {hash(str(d.embedding)) for d in docs_before}
        hash_set_updated= {hash(str(d.embedding)) for d in docs_updated}
        for doc in resp.search.docs:
            assert len(doc.matches) == 9
            for match in doc.matches:
                assert hash(str(match.embedding)) not in hash_set_before
                assert hash(str(match.embedding)) in hash_set_updated

    response_mock = mocker.Mock(wraps=validate_results)
    for method, docs in [
        ['index', docs_before],
        ['update', docs_updated]
    ]:
        with Flow.load_config('flow.yml') as index_flow:
            getattr(index_flow, method)(input_fn=(d for d in docs))


    with Flow.load_config('flow.yml') as search_flow:
        search_flow.search(input_fn=random_docs(NUMBER_OF_SEARCHES),
                           output_fn=response_mock)

    response_mock.assert_called()
