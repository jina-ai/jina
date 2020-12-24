import os
import random
import string
from itertools import chain

import numpy as np
import pytest

from jina import Document
from jina.flow import Flow
from jina.types.ndarray.generic import NdArray


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_TOPK_DIR'] = str(tmpdir)
    os.environ['JINA_TOPK'] = '9'
    yield
    del os.environ['JINA_TOPK_DIR']
    del os.environ['JINA_TOPK']


def random_docs(start, end, embed_dim=10, jitter=1, has_content=True):
    for j in range(start, end):
        d = Document()
        d.id = str(f'{j}' * 16)
        if has_content:
            d.tags['id'] = j
            d.text = ''.join(random.choice(string.ascii_lowercase) for _ in range(10)).encode('utf8')
            d.embedding = np.random.random([embed_dim + np.random.randint(0, jitter)])
        yield d


#TODO Test deletion of documents without content
@pytest.mark.parametrize('flow_file', [
    'flow.yml',
    'flow_vector.yml'
])
def test_delete(config, mocker, flow_file):
    NUMBER_OF_SEARCHES = 1

    def validate_result_factory(num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            for doc in resp.docs:
                assert len(doc.matches) == num_matches

        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(input_fn=random_docs(0, 10))

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(0, NUMBER_OF_SEARCHES),
                           output_fn=validate_result_factory(9))
    mock.assert_called_once()
    with Flow.load_config(flow_file) as index_flow:
        index_flow.delete(input_fn=random_docs(0, 10))
    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(0, NUMBER_OF_SEARCHES),
                           output_fn=validate_result_factory(0))
    mock.assert_called_once()


#TODO Test deletion of documents without content
@pytest.mark.parametrize('flow_file', [
    'flow_kv.yml',
])
def test_delete(config, mocker, flow_file):
    def validate_result_factory(num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == num_matches
        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(input_fn=random_docs(0, 10))

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=chain(random_docs(2,5), random_docs(100,120)),
                           output_fn=validate_result_factory(3))
    mock.assert_called_once()
    with Flow.load_config(flow_file) as index_flow:
        index_flow.delete(input_fn=random_docs(0, 10))
    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(2,4),
                           output_fn=validate_result_factory(0))
    mock.assert_called_once()


@pytest.mark.parametrize('flow_file', [
    'flow.yml',
    'flow_kv.yml', #fails
    'flow_vector.yml' #fails
])
def test_update(config, mocker, flow_file):
    NUMBER_OF_SEARCHES = 1
    docs_before = list(random_docs(0, 10))
    docs_updated = list(random_docs(0, 10))

    def validate_result_factory(has_changed):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            hash_set_before = {hash(str(d.embedding)) for d in docs_before}
            hash_set_updated = {hash(str(d.embedding)) for d in docs_updated}
            print('hash before', hash_set_before)
            print('hash updated', hash_set_updated)
            print('resp.docs', len(resp.docs))
            for doc in resp.docs:
                print('doc matches ', len(doc.matches))
                assert len(doc.matches) == 9
                for match in doc.matches:
                    h = hash(str(match.embedding))
                    print('match: ', h)
                    if has_changed:
                        assert h not in hash_set_before
                        assert h in hash_set_updated
                    else:
                        assert h in hash_set_before
                        assert h not in hash_set_updated
        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(input_fn=docs_before)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_docs = list(random_docs(0, NUMBER_OF_SEARCHES))
        print('search docs', [hash(str(d.embedding)) for d in search_docs])
        search_flow.search(input_fn=search_docs,
                           output_fn=validate_result_factory(has_changed=False))
    mock.assert_called_once()

    with Flow.load_config(flow_file) as index_flow:
        index_flow.update(input_fn=docs_updated)
    mock = mocker.Mock()
    response_mock = mocker.Mock(wraps=validate_result_factory(has_changed=True))
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(0, NUMBER_OF_SEARCHES),
                           output_fn=response_mock)

    mock.assert_called_once()
