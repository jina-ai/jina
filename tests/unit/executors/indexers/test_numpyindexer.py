import os

import numpy as np
import pytest

from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector import NumpyIndexer
# fix the seed here

np.random.seed(500)
retr_idx = None
num_data = 100
num_dim = 64
num_query = 10
vec_idx = np.random.randint(0, high=num_data, size=[num_data])
vec = np.random.random([num_data, num_dim])
query = np.array(np.random.random([num_query, num_dim]), dtype=np.float32)
cur_dir = os.path.dirname(os.path.abspath(__file__))

@pytest.mark.parametrize('batch_size, compress_level', [(None, 0), (None, 1), (2, 0), (2, 1)])
def test_numpy_indexer(batch_size, compress_level, test_metas):
    with NumpyIndexer(index_filename='np.test.gz', compress_level=compress_level, metas=test_metas) as indexer:
        indexer.batch_size = batch_size
        indexer.add(vec_idx, vec)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        idx, dist = indexer.query(query, top_k=4)
        global retr_idx
        if retr_idx is None:
            retr_idx = idx
        else:
            np.testing.assert_almost_equal(retr_idx, idx)
        assert idx.shape == dist.shape
        assert idx.shape == (num_query, 4)


@pytest.mark.parametrize('batch_size, compress_level', [(None, 0), (None, 1), (16, 0), (16, 1)])
def test_numpy_indexer_known(batch_size, compress_level, test_metas):
    vectors = np.array([[1, 1, 1],
                        [10, 10, 10],
                        [100, 100, 100],
                        [1000, 1000, 1000]])
    keys = np.array([4, 5, 6, 7]).reshape(-1, 1)
    with NumpyIndexer(index_filename='np.test.gz', compress_level=compress_level, metas=test_metas) as indexer:
        indexer.batch_size = batch_size
        indexer.add(keys, vectors)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    queries = np.array([[1, 1, 1],
                        [10, 10, 10],
                        [100, 100, 100],
                        [1000, 1000, 1000]])
    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        idx, dist = indexer.query(queries, top_k=2)
        np.testing.assert_equal(idx, np.array([[4, 5], [5, 4], [6, 5], [7, 6]]))
        assert idx.shape == dist.shape
        assert idx.shape == (4, 2)
        np.testing.assert_equal(indexer.query_by_id([7, 4]), vectors[[3, 0]])


@pytest.mark.parametrize('batch_size, compress_level', [(None, 0), (None, 1), (16, 0), (16, 1)])
def test_scipy_indexer(batch_size, compress_level, test_metas):
    with NumpyIndexer(index_filename='np.test.gz', backend='scipy', compress_level=compress_level, metas=test_metas) as indexer:
        indexer.batch_size = batch_size
        indexer.add(vec_idx, vec)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        idx, dist = indexer.query(query, top_k=4)
        global retr_idx
        if retr_idx is None:
            retr_idx = idx
        else:
            np.testing.assert_almost_equal(retr_idx, idx)
        assert idx.shape == dist.shape
        assert idx.shape == (num_query, 4)
