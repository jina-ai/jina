import os
import random
import string

import numpy as np
import pytest

from jina import Document, Flow

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
        d.text = ''.join(random.choice(string.ascii_lowercase) for _ in range(10)).encode('utf8')
        d.embedding = np.random.random([embed_dim])
        yield d


# fails #TODO fix related issue
def test_search_non_existent(config, mocker):
    yaml_file = 'index_kv_simple.yml'

    def validate_results(resp):
        mock()
        assert len(resp.docs) == 3

    with Flow().add(
            uses=os.path.join(cur_dir, 'yaml', yaml_file),
            shards=2,
            separated_workspace=True,
    ) as index_flow:
        index_flow.index(input_fn=random_docs(0, 3), request_size=1)

    mock = mocker.Mock()
    with Flow(read_only=True).add(
            uses=os.path.join(cur_dir, 'yaml', yaml_file),
            shards=2,
            separated_workspace=True,
            uses_after=os.path.join(cur_dir, 'yaml', 'merge_root.yml'),
            polling='all'
    ) as search_flow:
        search_flow.search(input_fn=random_docs(0, 5),
                           output_fn=validate_results,
                           request_size=5
                           )
    mock.assert_called_once()
