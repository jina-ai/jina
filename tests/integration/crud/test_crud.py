import os
import random
import string
from itertools import chain
from pathlib import Path

import numpy as np
import pytest
from jina.executors.indexers import BaseIndexer

from jina import Document
from jina.flow import Flow

random.seed(0)
np.random.seed(0)


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


def validate_index_size(num_indexed_docs):
    path = Path(os.environ['JINA_TOPK_DIR'])
    index_files = list(path.glob('*.bin'))
    assert len(index_files) > 0
    for index_file in index_files:
        index = BaseIndexer.load(str(index_file))
        assert index.size == num_indexed_docs


@pytest.mark.parametrize('flow_file, has_content', [
    ['flow.yml', True],
    ['flow_vector.yml', True],
    ['flow.yml', False],
    ['flow_vector.yml', False]
])
def test_delete_vector(config, mocker, flow_file, has_content):
    NUMBER_OF_SEARCHES = 5

    def validate_result_factory(num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            for doc in resp.docs:
                assert len(doc.matches) == num_matches

        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(input_fn=random_docs(0, 10))
    validate_index_size(10)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(0, NUMBER_OF_SEARCHES),
                           output_fn=validate_result_factory(9))
    mock.assert_called_once()

    with Flow.load_config(flow_file) as index_flow:
        index_flow.delete(input_fn=random_docs(0, 10, has_content=has_content))
    validate_index_size(0)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(0, NUMBER_OF_SEARCHES),
                           output_fn=validate_result_factory(0))
    mock.assert_called_once()


@pytest.mark.parametrize('has_content', [True, False])
def test_delete_kv(config, mocker, has_content):
    flow_file = 'flow_kv.yml'

    def validate_result_factory(num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == num_matches

        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(input_fn=random_docs(0, 10))
    validate_index_size(10)
    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=chain(random_docs(2, 5), random_docs(100, 120)),
                           output_fn=validate_result_factory(3))
    mock.assert_called_once()

    with Flow.load_config(flow_file) as index_flow:
        index_flow.delete(input_fn=random_docs(0, 3, has_content=has_content))
    validate_index_size(7)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(2, 4),
                           output_fn=validate_result_factory(1))
    mock.assert_called_once()


@pytest.mark.parametrize('flow_file', [
    'flow.yml',
    'flow_vector.yml'
])
def test_update_vector(config, mocker, flow_file):
    NUMBER_OF_SEARCHES = 1
    docs_before = list(random_docs(0, 10))
    docs_updated = list(random_docs(0, 10))

    def validate_result_factory(has_changed):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            hash_set_before = [hash(d.embedding.tobytes()) for d in docs_before]
            hash_set_updated = [hash(d.embedding.tobytes()) for d in docs_updated]
            for doc in resp.docs:
                assert len(doc.matches) == 9
                for match in doc.matches:
                    h = hash(match.embedding.tobytes())
                    if has_changed:
                        assert h not in hash_set_before
                        assert h in hash_set_updated
                    else:
                        assert h in hash_set_before
                        assert h not in hash_set_updated

        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(
            input_fn=docs_before
        )
    validate_index_size(10)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_docs = list(random_docs(0, NUMBER_OF_SEARCHES))
        search_flow.search(input_fn=search_docs,
                           output_fn=validate_result_factory(has_changed=False))
    mock.assert_called_once()

    with Flow.load_config(flow_file) as index_flow:
        index_flow.update(input_fn=docs_updated)
    validate_index_size(10)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(0, NUMBER_OF_SEARCHES),
                           output_fn=validate_result_factory(has_changed=True))
    mock.assert_called_once()


def test_update_kv(config, mocker):
    flow_file = 'flow_kv.yml'
    NUMBER_OF_SEARCHES = 1
    docs_before = list(random_docs(0, 10))
    docs_updated = list(random_docs(0, 10))

    def validate_results(resp):
        mock()
        assert len(resp.docs) == NUMBER_OF_SEARCHES

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(
            input_fn=docs_before
        )
    validate_index_size(10)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_docs = list(random_docs(0, NUMBER_OF_SEARCHES))
        search_flow.search(input_fn=search_docs,
                           output_fn=validate_results)
    mock.assert_called_once()

    with Flow.load_config(flow_file) as index_flow:
        index_flow.update(input_fn=docs_updated)
    validate_index_size(10)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=random_docs(0, NUMBER_OF_SEARCHES),
                           output_fn=validate_results)
    mock.assert_called_once()
