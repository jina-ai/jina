import os
import random
import string
from pathlib import Path

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


def test_simple_index(config):
    yaml_file = 'index_kv_simple.yml'
    index_name = 'kvidx'

    def generate_docs():
        for j in range(3):
            d = Document()
            d.id = f'{j:0>16}'
            d.tags['id'] = j
            yield d

    with Flow().add(
            uses=os.path.join(cur_dir, 'yaml', yaml_file),
            shards=2
    ) as index_flow:
        index_flow.index(input_fn=generate_docs(), request_size=1)

    expected_count_list = [2, 1]
    expected_count_list.sort()
    path = Path(os.environ['JINA_SHARDING_DIR'])
    index_files = list(path.glob(f'{index_name}.bin')) + list(path.glob(f'*/{index_name}.bin'))
    assert len(index_files) > 0
    assert len(index_files) == len(expected_count_list)
