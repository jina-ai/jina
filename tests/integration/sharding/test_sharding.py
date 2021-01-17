import os
import random
import string
from pathlib import Path

import numpy as np
import pytest

from jina import Document
from jina.executors.indexers import BaseIndexer
from jina.flow import Flow

random.seed(0)
np.random.seed(0)


def get_index_flow(yaml_file, num_shards):
    f = Flow().add(
        uses='yaml/' + yaml_file,
        shards=num_shards,
        separated_workspace=True,
    )
    return f


def get_delete_flow(yaml_file, num_shards):
    f = Flow().add(
        uses='yaml/' + yaml_file,
        shards=num_shards,
        separated_workspace=True,
        polling='all',
    )
    return f


def get_update_flow(yaml_file, num_shards):
    f = Flow().add(
        uses='yaml/' + yaml_file,
        shards=num_shards,
        separated_workspace=True,
        polling='all',
    )
    return f


def get_search_flow(yaml_file, num_shards):
    f = Flow(read_only=True).add(
        uses='yaml/' + yaml_file,
        shards=num_shards,
        separated_workspace=True,
        uses_after='_merge_matches_topk',
        polling='all',
        timeout_ready='-1'
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
            d.text = ''.join(random.choice(string.ascii_lowercase) for _ in range(10)).encode('utf8')
            d.embedding = np.random.random([embed_dim])
            d.chunks.append(c)
        d.text = ''.join(random.choice(string.ascii_lowercase) for _ in range(10)).encode('utf8')
        d.embedding = np.random.random([embed_dim])
        yield d


def validate_index_size(expected_count_list, index_name):
    expected_count_list.sort()
    path = Path(os.environ['JINA_SHARDING_DIR'])
    index_files = list(path.glob(f'{index_name}.bin')) + list(path.glob(f'*/{index_name}.bin'))
    assert len(index_files) > 0
    actual_count_list = []
    assert len(index_files) == len(expected_count_list)
    for index_file, count in zip(index_files, expected_count_list):
        index = BaseIndexer.load(str(index_file))
        actual_count_list.append(index.size)
    actual_count_list.sort()
    assert actual_count_list == expected_count_list


@pytest.mark.parametrize(
    'num_shards, expected1, expected2', (
            (1, [201], [121]),
            (2, [101, 100], [71, 50]),
            (3, [100, 100, 1], [70, 50, 1]),
            (10, [100, 100, 1], [70, 50, 1]),
    )
)
@pytest.mark.parametrize('index_conf, index_names', [
    ['index.yml', ['kvidx', 'vecidx']],
    ['index_vector.yml', ['vecidx']]
])
def test_delete_vector(config, mocker, index_conf, index_names, num_shards, expected1, expected2):
    def validate_result_factory(num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == 7
            for doc in resp.docs:
                assert len(doc.matches) == num_matches

        return validate_results

    with get_index_flow(index_conf, num_shards) as index_flow:
        index_flow.index(input_fn=random_docs(0, 201))

    for index_name in index_names:
        validate_index_size(expected1, index_name)

    with get_delete_flow(index_conf, num_shards) as index_flow:
        index_flow.delete(input_fn=random_docs(0, 30))

    with get_delete_flow(index_conf, num_shards) as index_flow:
        index_flow.delete(input_fn=random_docs(100, 150))

    for index_name in index_names:
        validate_index_size(expected2, index_name)

    mock = mocker.Mock()
    with get_search_flow(index_conf, num_shards) as search_flow:
        search_flow.search(input_fn=random_docs(28, 35),
                           output_fn=validate_result_factory(10))
    mock.assert_called_once()


@pytest.mark.parametrize(
    'num_shards, expected1, expected2', (
            (1, [201], [121]),
            (2, [101, 100], [71, 50]),
            (3, [100, 100, 1], [70, 50, 1]),
            (10, [100, 100, 1], [70, 50, 1, 0, 0, 0, 0, 0, 0, 0]),
    )
)
def test_delete_kv(config, mocker, num_shards, expected1, expected2):
    index_conf = 'index_kv.yml'
    index_name = 'kvidx'

    def validate_result_factory(num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == num_matches

        return validate_results

    with get_index_flow(index_conf, num_shards) as index_flow:
        index_flow.index(input_fn=random_docs(0, 201))

    validate_index_size(expected1, index_name)

    with get_delete_flow(index_conf, num_shards) as delete_flow:
        delete_flow.delete(input_fn=random_docs(0, 30))

    with get_delete_flow(index_conf, num_shards) as delete_flow:
        delete_flow.delete(input_fn=random_docs(100, 150))

    validate_index_size(expected2, index_name)

    mock = mocker.Mock()
    with get_search_flow(index_conf, num_shards) as search_flow:
        search_flow.search(
            input_fn=random_docs(28, 35),
            output_fn=validate_result_factory(5))
    mock.assert_called_once()


@pytest.mark.parametrize(
    'num_shards, expected_size_1, expected_size_2', (
            (1, [201], [201]),
            (2, [101, 100], [101, 100]),
            (3, [100, 100, 1], [100, 100, 1]),
            (10, [100, 100, 1], [100, 100, 1]),
    )
)
@pytest.mark.parametrize('index_conf, index_names', [
    ['index.yml', ['kvidx', 'vecidx']],
    ['index_vector.yml', ['vecidx']]
])
def test_update_vector(config, mocker, index_conf, index_names, num_shards, expected_size_1, expected_size_2):
    docs_before = list(random_docs(0, 201))
    docs_updated = list(random_docs(0, 210))
    hash_set_before = [hash(d.embedding.tobytes()) for d in docs_before]
    hash_set_updated = [hash(d.embedding.tobytes()) for d in docs_updated]

    def validate_result_factory():
        def validate_results(resp):
            mock()
            assert len(resp.docs) == 1
            for doc in resp.docs:
                assert len(doc.matches) == 10
                for match in doc.matches:
                    h = hash(match.embedding.tobytes())
                    assert h not in hash_set_before
                    assert h in hash_set_updated

        return validate_results

    with get_index_flow(index_conf, num_shards) as index_flow:
        index_flow.index(input_fn=docs_before)

    for index_name in index_names:
        validate_index_size(expected_size_1, index_name)

    with get_update_flow(index_conf, num_shards) as update_flow:
        update_flow.update(input_fn=docs_updated)

    for index_name in index_names:
        validate_index_size(expected_size_2, index_name)

    mock = mocker.Mock()

    with get_search_flow(index_conf, num_shards) as search_flow:
        search_flow.search(
            input_fn=random_docs(0, 1),
            output_fn=validate_result_factory())
    assert mock.call_count == 1


@pytest.mark.parametrize(
    'num_shards, expected_size_1, expected_size_2', (
            (1, [201], [201]),
            (2, [101, 100], [101, 100]),
            (3, [100, 100, 1], [100, 100, 1]),  # Flaky
            (10, [100, 100, 1], [100, 100, 1, 0, 0, 0, 0, 0, 0, 0]),
    )
)
def test_update_kv(config, mocker, num_shards, expected_size_1, expected_size_2):
    index_conf = 'index_kv.yml'
    index_name = 'kvidx'

    docs_before = list(random_docs(0, 201))
    docs_updated = list(random_docs(190, 210))
    hash_set_before = [hash(d.embedding.tobytes()) for d in docs_before]
    hash_set_updated = [hash(d.embedding.tobytes()) for d in docs_updated]

    def validate_results_1(resp):
        mock()
        assert len(resp.docs) == 100
        for i, doc in enumerate(resp.docs):
            h = hash(doc.embedding.tobytes())

            assert h in hash_set_before
            assert h not in hash_set_updated

    def validate_results_2(resp):
        mock()
        assert len(resp.docs) == 100
        for i, doc in enumerate(resp.docs):
            h = hash(doc.embedding.tobytes())
            if i < 90:
                assert h in hash_set_before
                assert h not in hash_set_updated
            else:
                assert h not in hash_set_before
                assert h in hash_set_updated

    def validate_results_3(resp):
        mock()
        assert len(resp.docs) == 1
        h = hash(resp.docs[0].embedding.tobytes())
        assert h not in hash_set_before
        assert h in hash_set_updated

    with get_index_flow(index_conf, num_shards) as index_flow:
        index_flow.index(input_fn=docs_before)

    validate_index_size(expected_size_1, index_name)

    with get_update_flow(index_conf, num_shards) as update_flow:
        update_flow.update(input_fn=docs_updated)

    validate_index_size(expected_size_2, index_name)

    mock = mocker.Mock()
    for start, end, validate_results in (
            (0, 100, validate_results_1),
            (100, 200, validate_results_2),
            (200, 201, validate_results_3)
    ):
        with get_search_flow(index_conf, num_shards) as search_flow:
            search_flow.search(input_fn=random_docs(start, end),
                               output_fn=validate_results)
    assert mock.call_count == 3
