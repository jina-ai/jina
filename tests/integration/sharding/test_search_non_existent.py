import os
import random
import string

import numpy as np
import pytest

from jina import Document, Flow

from tests import validate_callback

random.seed(0)
np.random.seed(0)

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_SHARDING_DIR'] = str(tmpdir)
    yield
    del os.environ['JINA_SHARDING_DIR']


def random_docs(start, end, embed_dim=10):
    for j in range(start, end):
        d = Document()
        d.id = f'{j:0>16}'
        d.tags['id'] = j
        d.text = ''.join(
            random.choice(string.ascii_lowercase) for _ in range(10)
        ).encode('utf8')
        d.embedding = np.random.random([embed_dim])
        yield d


def test_search_non_existent(config, mocker):
    yaml_file = 'index_kv_simple.yml'

    def validate_results(resp):
        assert len(resp.docs) == 3

    with Flow().add(
        uses=os.path.join(cur_dir, 'yaml', yaml_file),
        shards=2,
    ) as index_flow:
        index_flow.index(inputs=random_docs(0, 3), request_size=1)

    mock = mocker.Mock()
    with Flow(read_only=True).add(
        uses=os.path.join(cur_dir, 'yaml', yaml_file),
        shards=2,
        uses_after='_merge_root',
        polling='all',
    ) as search_flow:
        search_flow.search(inputs=random_docs(0, 5), on_done=mock, request_size=5)

    mock.assert_called_once()
    validate_callback(mock, validate_results)
