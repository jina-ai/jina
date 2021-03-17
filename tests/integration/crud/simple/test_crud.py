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

from tests import validate_callback

random.seed(0)
np.random.seed(0)

TOPK = 9


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_TOPK_DIR'] = str(tmpdir)
    os.environ['JINA_TOPK'] = str(TOPK)
    yield
    del os.environ['JINA_TOPK_DIR']
    del os.environ['JINA_TOPK']


def random_docs(start, end, embed_dim=10, jitter=1, has_content=True):
    for j in range(start, end):
        d = Document()
        d.id = j
        if has_content:
            d.tags['id'] = j
            d.text = ''.join(
                random.choice(string.ascii_lowercase) for _ in range(10)
            ).encode('utf8')
            d.embedding = np.random.random([embed_dim + np.random.randint(0, jitter)])
        yield d


def get_ids_to_delete(start, end, as_string):
    if as_string:
        return (str(idx) for idx in range(start, end))
    return range(start, end)


def validate_index_size(num_indexed_docs, compound=False):
    from jina.executors.compound import CompoundExecutor

    if compound:
        path = Path(
            CompoundExecutor.get_component_workspace_from_compound_workspace(
                os.environ['JINA_TOPK_DIR'], 'chunk_indexer', 0
            )
        )
    else:
        path = Path(os.environ['JINA_TOPK_DIR'])
    bin_files = list(path.glob('*.bin'))
    assert len(bin_files) > 0
    for index_file in bin_files:
        index = BaseIndexer.load(str(index_file))
        assert index.size == num_indexed_docs


@pytest.mark.parametrize(
    'flow_file, has_content, compound',
    [
        ['flow.yml', True, True],
        ['flow_vector.yml', True, False],
        ['flow.yml', False, True],
        ['flow_vector.yml', False, False],
    ],
)
def test_delete_vector(config, mocker, flow_file, has_content, compound):
    NUMBER_OF_SEARCHES = 5

    def validate_result_factory(num_matches):
        def validate_results(resp):
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            for doc in resp.docs:
                assert len(doc.matches) == num_matches

        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(inputs=random_docs(0, 10))
    validate_index_size(10, compound)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(inputs=random_docs(0, NUMBER_OF_SEARCHES), on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(TOPK))

    delete_ids = []
    for d in random_docs(0, 10, has_content=has_content):
        delete_ids.append(d.id)
        for c in d.chunks:
            delete_ids.append(c.id)

    with Flow.load_config(flow_file) as index_flow:
        index_flow.delete(ids=delete_ids)
    validate_index_size(0, compound)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(inputs=random_docs(0, NUMBER_OF_SEARCHES), on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(0))


@pytest.mark.parametrize('as_string', [True, False])
def test_delete_kv(config, mocker, as_string):
    flow_file = 'flow_kv.yml'

    def validate_result_factory(num_matches):
        def validate_results(resp):
            assert len(resp.docs) == num_matches

        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(inputs=random_docs(0, 10))
    validate_index_size(10)
    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(
            inputs=chain(random_docs(2, 5), random_docs(100, 120)), on_done=mock
        )
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(3))

    with Flow.load_config(flow_file) as index_flow:
        index_flow.delete(ids=get_ids_to_delete(0, 3, as_string))
    validate_index_size(7)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(inputs=random_docs(2, 4), on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(1))


@pytest.mark.parametrize(
    'flow_file, compound', [('flow.yml', True), ('flow_vector.yml', False)]
)
def test_update_vector(config, mocker, flow_file, compound):
    NUMBER_OF_SEARCHES = 1
    docs_before = list(random_docs(0, 10))
    docs_updated = list(random_docs(0, 10))

    def validate_result_factory(has_changed):
        def validate_results(resp):
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            hash_set_before = [hash(d.embedding.tobytes()) for d in docs_before]
            hash_set_updated = [hash(d.embedding.tobytes()) for d in docs_updated]
            for doc in resp.docs:
                assert len(doc.matches) == TOPK
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
        index_flow.index(inputs=docs_before)
    validate_index_size(10, compound)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_docs = list(random_docs(0, NUMBER_OF_SEARCHES))
        search_flow.search(inputs=search_docs, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(has_changed=False))

    with Flow.load_config(flow_file) as index_flow:
        index_flow.update(inputs=docs_updated)
    validate_index_size(10, compound)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(inputs=random_docs(0, NUMBER_OF_SEARCHES), on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(has_changed=True))


def test_update_kv(config, mocker):
    flow_file = 'flow_kv.yml'
    NUMBER_OF_SEARCHES = 1
    docs_before = list(random_docs(0, 10))
    docs_updated = list(random_docs(0, 10))

    def validate_results(resp):
        assert len(resp.docs) == NUMBER_OF_SEARCHES

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(inputs=docs_before)
    validate_index_size(10)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_docs = list(random_docs(0, NUMBER_OF_SEARCHES))
        search_flow.search(inputs=search_docs, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_results)

    with Flow.load_config(flow_file) as index_flow:
        index_flow.update(inputs=docs_updated)
    validate_index_size(10)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(inputs=random_docs(0, NUMBER_OF_SEARCHES), on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_results)
