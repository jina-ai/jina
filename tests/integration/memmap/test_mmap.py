import json

import numpy as np
import pytest

from jina.executors.indexers.vector import NumpyIndexer
from jina.helper import get_readable_size
from jina.logging.profile import used_memory_readable, TimeContext, used_memory
from tests import rm_files

num_data = 10000
num_dim = 10000
queries = np.random.random([100, num_dim])
vec_idx = np.random.randint(0, high=num_data, size=[num_data])
vec = np.random.random([num_data, num_dim])
filename = 'a.gz'
summary_file = 'summary.json'


@pytest.mark.run(order=3)
@pytest.mark.timeout(360)
def test_standard():
    with NumpyIndexer(index_filename=filename, compress_level=0) as ni:
        ni.batch_size = 512
        ni.add(vec_idx, vec)
        ni.save('a.bin')


@pytest.mark.run(order=4)
@pytest.mark.timeout(360)
def test_standard_query():
    mem1 = used_memory(1)
    print(used_memory_readable())
    with NumpyIndexer.load('a.bin') as ni:
        ni.batch_size = 256
        print(used_memory_readable())
        print(ni.raw_ndarray.shape)
        print(used_memory_readable())
        with TimeContext('query topk') as ti:
            result = ni.query(queries, top_k=10)
            mem2 = used_memory(1)
            print(used_memory_readable())
            print(result[0].shape)
        with open(summary_file, 'a') as fp:
            json.dump({'name': 'naive',
                       'memory': mem2 - mem1,
                       'readable': get_readable_size(mem2 - mem1),
                       'time': ti.duration}, fp)
            fp.write('\n')

    rm_files([ni.index_abspath, ni.save_abspath, 'a.bin', 'a.gz'])
