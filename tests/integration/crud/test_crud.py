import os
import random
import string

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


def random_docs(num_docs, embed_dim=10, jitter=1, has_content=True):
    for j in range(num_docs):
        d = jina_pb2.DocumentProto()
        d.id = str(f'{j}' * 16)
        if has_content:
            d.tags['id'] = j
            d.text = ''.join(random.choice(string.ascii_lowercase) for _ in range(10)).encode('utf8')
            NdArray(d.embedding).value = np.random.random([embed_dim + np.random.randint(0, jitter)])
        yield d


@pytest.mark.parametrize('flow_file', [
    'flow.yml',
    'flow_kv.yml', #fails
    'flow_vector.yml'
])
def test_delete(config, mocker, flow_file):
    NUMBER_OF_SEARCHES = 3

    def validate_result_factory(num_matches):
        def validate_results(resp):
            assert len(resp.search.docs) == NUMBER_OF_SEARCHES
            for doc in resp.search.docs:
                assert len(doc.matches) == num_matches

        return validate_results

    docs_before = list(random_docs(10))
    docs_deleted = list(random_docs(10, has_content=False))

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(input_fn=docs_before)

    response_mock = mocker.Mock(wraps=validate_result_factory(9))
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(NUMBER_OF_SEARCHES),
                           output_fn=response_mock)

    with Flow.load_config(flow_file) as index_flow:
        index_flow.delete(input_fn=docs_deleted)

    response_mock = mocker.Mock(wraps=validate_result_factory(0))
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(NUMBER_OF_SEARCHES),
                           output_fn=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('flow_file', [
    'flow.yml',
    'flow_kv.yml', #fails
    'flow_vector.yml' #fails
])
def test_update(config, mocker, flow_file):
    NUMBER_OF_SEARCHES = 3
    docs_before = list(random_docs(10))
    docs_updated = list(random_docs(10))

    def validate_result_factory(has_changed):
        def validate_results(resp):
            print('start validation')
            assert len(resp.search.docs) == NUMBER_OF_SEARCHES
            hash_set_before = {hash(str(d.embedding)) for d in docs_before}
            hash_set_updated = {hash(str(d.embedding)) for d in docs_updated}
            for doc in resp.search.docs:
                assert len(doc.matches) == 9
                for match in doc.matches:
                    if has_changed:
                        assert hash(str(match.embedding)) not in hash_set_before
                        assert hash(str(match.embedding)) in hash_set_updated
                    else:
                        assert hash(str(match.embedding)) in hash_set_before
                        assert hash(str(match.embedding)) not in hash_set_updated

        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(input_fn=docs_before)
    response_mock = mocker.Mock(wraps=validate_result_factory(has_changed=False))

    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(NUMBER_OF_SEARCHES),
                           output_fn=response_mock)

    with Flow.load_config(flow_file) as index_flow:
        index_flow.update(input_fn=docs_updated)

    response_mock = mocker.Mock(wraps=validate_result_factory(has_changed=True))
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(NUMBER_OF_SEARCHES),
                           output_fn=response_mock)

    response_mock.assert_called()
