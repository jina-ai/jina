import os
import random
import string
from pathlib import Path

import numpy as np
import pytest

from jina import Document
from jina.executors.indexers import BaseIndexer
from jina.flow import Flow

from tests import validate_callback

random.seed(0)
np.random.seed(0)

cur_dir = os.path.dirname(os.path.abspath(__file__))


def get_index_flow(yaml_file, num_shards):
    f = Flow().add(
        uses=os.path.join(cur_dir, 'yaml', yaml_file),
        shards=num_shards,
    )
    return f


def get_delete_flow(yaml_file, num_shards):
    f = Flow().add(
        uses=os.path.join(cur_dir, 'yaml', yaml_file),
        shards=num_shards,
        polling='all',
    )
    return f


def get_update_flow(yaml_file, num_shards):
    f = Flow().add(
        uses=os.path.join(cur_dir, 'yaml', yaml_file),
        shards=num_shards,
        polling='all',
    )
    return f


def get_search_flow(yaml_file, num_shards, uses_after='_merge_matches_topk'):
    f = Flow(read_only=True).add(
        uses=os.path.join(cur_dir, 'yaml', yaml_file),
        shards=num_shards,
        uses_after=uses_after,
        polling='all',
        timeout_ready='-1',
    )
    return f


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_SHARDING_DIR'] = str(tmpdir)
    os.environ['JINA_TOPK'] = '10'
    yield
    del os.environ['JINA_SHARDING_DIR']
    del os.environ['JINA_TOPK']


def random_docs(start, end, embed_dim=10):
    for j in range(start, end):
        d = Document()
        d.id = f'{j:0>16}'
        d.tags['id'] = j
        for i in range(5):
            c = Document()
            c.id = f'{j:0>16}'
            d.text = ''.join(
                random.choice(string.ascii_lowercase) for _ in range(10)
            ).encode('utf8')
            d.embedding = np.random.random([embed_dim])
            d.chunks.append(c)
        d.text = ''.join(
            random.choice(string.ascii_lowercase) for _ in range(10)
        ).encode('utf8')
        d.embedding = np.random.random([embed_dim])
        yield d


def validate_index_size(expected_count, index_name):
    path = Path(os.environ['JINA_SHARDING_DIR'])
    index_files = list(path.glob(f'{index_name}.bin')) + list(
        path.glob(f'*/{index_name}.bin')
    )
    assert len(index_files) > 0
    actual_count_list = []
    assert len(index_files) > 0
    count_sum = 0
    for index_file in index_files:
        index = BaseIndexer.load(str(index_file))
        count_sum += index.size
    actual_count_list.sort()
    assert count_sum == expected_count


@pytest.mark.parametrize('num_shards', (1, 2, 3, 10))
@pytest.mark.parametrize(
    'index_conf, index_names',
    [['index.yml', ['kvidx', 'vecidx']], ['index_vector.yml', ['vecidx']]],
)
def test_delete_vector(config, mocker, index_conf, index_names, num_shards):
    def _validate_result_factory(num_matches):
        def _validate_results(resp):
            assert len(resp.docs) == 7
            for doc in resp.docs:
                assert len(doc.matches) == num_matches

        return _validate_results

    with get_index_flow(index_conf, num_shards) as index_flow:
        index_flow.index(inputs=random_docs(0, 201), request_size=100)

    for index_name in index_names:
        validate_index_size(201, index_name)

    with get_delete_flow(index_conf, num_shards) as index_flow:
        index_flow.delete(ids=[d.id for d in random_docs(0, 30)], request_size=100)

    with get_delete_flow(index_conf, num_shards) as index_flow:
        index_flow.delete(ids=[d.id for d in random_docs(100, 150)], request_size=100)

    for index_name in index_names:
        validate_index_size(121, index_name)

    mock = mocker.Mock()
    with get_search_flow(index_conf, num_shards) as search_flow:
        search_flow.search(inputs=random_docs(28, 35), on_done=mock, request_size=100)
    mock.assert_called_once()
    validate_callback(mock, _validate_result_factory(10))


@pytest.mark.parametrize('num_shards', (1, 2, 3, 10))
def test_delete_kv(config, mocker, num_shards):
    index_conf = 'index_kv.yml'
    index_name = 'kvidx'

    def _validate_result_factory(num_matches):
        def _validate_results(resp):
            assert len(resp.docs) == num_matches

        return _validate_results

    with get_index_flow(index_conf, num_shards) as index_flow:
        index_flow.index(inputs=random_docs(0, 201), request_size=100)

    validate_index_size(201, index_name)

    with get_delete_flow(index_conf, num_shards) as delete_flow:
        delete_flow.delete(ids=[d.id for d in random_docs(0, 30)], request_size=100)

    with get_delete_flow(index_conf, num_shards) as delete_flow:
        delete_flow.delete(ids=[d.id for d in random_docs(100, 150)], request_size=100)

    validate_index_size(121, index_name)

    mock = mocker.Mock()
    with get_search_flow(index_conf, num_shards, '_merge_root') as search_flow:
        search_flow.search(inputs=random_docs(28, 35), on_done=mock, request_size=100)
    mock.assert_called_once()
    validate_callback(mock, _validate_result_factory(5))


@pytest.mark.parametrize(
    'num_shards',
    (1, 2, 3, 10),
)
@pytest.mark.parametrize(
    'index_conf, index_names',
    [['index.yml', ['kvidx', 'vecidx']], ['index_vector.yml', ['vecidx']]],
)
def test_update_vector(config, mocker, index_conf, index_names, num_shards):
    docs_before = list(random_docs(0, 201))
    docs_updated = list(random_docs(0, 210))
    hash_set_before = [hash(d.embedding.tobytes()) for d in docs_before]
    hash_set_updated = [hash(d.embedding.tobytes()) for d in docs_updated]

    def _validate_result_factory():
        def _validate_results(resp):
            assert len(resp.docs) == 1
            for doc in resp.docs:
                assert len(doc.matches) == 10
                for match in doc.matches:
                    h = hash(match.embedding.tobytes())
                    assert h not in hash_set_before
                    assert h in hash_set_updated

        return _validate_results

    with get_index_flow(index_conf, num_shards) as index_flow:
        index_flow.index(inputs=docs_before, request_size=100)

    for index_name in index_names:
        validate_index_size(201, index_name)

    with get_update_flow(index_conf, num_shards) as update_flow:
        update_flow.update(inputs=docs_updated, request_size=100)

    for index_name in index_names:
        validate_index_size(201, index_name)

    mock = mocker.Mock()

    with get_search_flow(index_conf, num_shards) as search_flow:
        search_flow.search(inputs=random_docs(0, 1), on_done=mock, request_size=100)
    mock.assert_called_once()
    validate_callback(mock, _validate_result_factory())


@pytest.mark.parametrize('num_shards', (1, 2, 3, 10))
def test_update_kv(config, mocker, num_shards):
    index_conf = 'index_kv.yml'
    index_name = 'kvidx'

    docs_before = list(random_docs(0, 201))
    docs_updated = list(random_docs(190, 210))
    hash_set_before = [hash(d.embedding.tobytes()) for d in docs_before]
    hash_set_updated = [hash(d.embedding.tobytes()) for d in docs_updated]

    def _validate_results_1(resp):
        assert len(resp.docs) == 100
        for i, doc in enumerate(resp.docs):
            h = hash(doc.embedding.tobytes())

            assert h in hash_set_before
            assert h not in hash_set_updated

    def _validate_results_2(resp):
        assert len(resp.docs) == 100
        for i, doc in enumerate(resp.docs):
            h = hash(doc.embedding.tobytes())
            if i < 90:
                assert h in hash_set_before
                assert h not in hash_set_updated
            else:
                assert h not in hash_set_before
                assert h in hash_set_updated

    def _validate_results_3(resp):
        assert len(resp.docs) == 1
        h = hash(resp.docs[0].embedding.tobytes())
        assert h not in hash_set_before
        assert h in hash_set_updated

    with get_index_flow(index_conf, num_shards) as index_flow:
        index_flow.index(inputs=docs_before, request_size=100)

    validate_index_size(201, index_name)

    with get_update_flow(index_conf, num_shards) as update_flow:
        update_flow.update(inputs=docs_updated, request_size=100)

    validate_index_size(201, index_name)

    for start, end, validate_results in (
        (0, 100, _validate_results_1),
        (100, 200, _validate_results_2),
        (200, 201, _validate_results_3),
    ):
        mock = mocker.Mock()
        with get_search_flow(index_conf, num_shards, '_merge_root') as search_flow:
            search_flow.search(
                inputs=random_docs(start, end), on_done=mock, request_size=100
            )
        validate_callback(mock, validate_results)
        mock.assert_called_once()
