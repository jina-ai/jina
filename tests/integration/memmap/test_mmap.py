import json

import numpy as np
import pytest

from jina.executors.indexers.mmap import MmapNumpyIndexer
from jina.executors.indexers.vector import NumpyIndexer
from jina.helper import get_readable_size
from jina.logging.profile import used_memory_readable, TimeContext, used_memory
from tests import rm_files

num_data = 10000
num_dim = 1000
queries = np.random.random([100, num_dim])
vec_idx = np.random.randint(0, high=num_data, size=[num_data])
vec = np.random.random([num_data, num_dim])
filename = 'a.gz'


@pytest.mark.run(order=5)
def test_check_summary():
    with open('summary.json') as fp:
        t = [json.loads(v) for v in fp]
        if t[0]['name'] == 'naive':
            assert t[0]['memory'] > t[1]['memory']
            assert t[0]['time'] > t[1]['time']
        else:
            assert t[0]['memory'] < t[1]['memory']
            assert t[0]['time'] < t[1]['time']


@pytest.mark.run(order=3)
def test_standard():
    with NumpyIndexer(index_filename=filename) as ni:
        ni.add(vec_idx, vec)
        ni.save('a.bin')


@pytest.mark.run(order=4)
def test_standard_query():
    mem1 = used_memory(1)
    with NumpyIndexer.load('a.bin') as ni:
        print(used_memory_readable())
        print(ni.raw_ndarray.shape)
        print(used_memory_readable())
        with TimeContext('query topk') as ti:
            ni.query(queries, top_k=10)
            mem2 = used_memory(1)
        with open('summary.txt', 'a') as fp:
            json.dump({'name': 'naive',
                       'memory': mem2 - mem1,
                       'readable': get_readable_size(mem2 - mem1),
                       'time': ti.duration}, fp)
            fp.write('\n')

    rm_files([ni.index_abspath, ni.save_abspath])


@pytest.mark.run(order=1)
def test_memmap():
    with MmapNumpyIndexer(index_filename=filename) as ni:
        ni.add(vec_idx, vec)
        ni.save('a.bin')


@pytest.mark.run(order=2)
def test_memmap_query():
    mem1 = used_memory(1)
    with MmapNumpyIndexer.load('a.bin') as ni:
        print(used_memory_readable())
        print(ni.raw_ndarray.shape)
        print(used_memory_readable())
        with TimeContext('query topk') as ti:
            ni.query(queries, top_k=10)
            mem2 = used_memory(1)
        with open('summary.json', 'a') as fp:
            json.dump({'name': 'memmap',
                       'memory': mem2 - mem1,
                       'readable': get_readable_size(mem2 - mem1),
                       'time': ti.duration}, fp)
            fp.write('\n')

    rm_files([ni.index_abspath, ni.save_abspath])
