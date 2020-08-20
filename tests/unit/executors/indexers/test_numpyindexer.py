import os
import shutil

import numpy as np

from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector import NumpyIndexer

# fix the seed here
np.random.seed(500)
retr_idx = None
vec_idx = np.random.randint(0, high=100, size=[10])
vec = np.random.random([10, 10])
query = np.array(np.random.random([10, 10]), dtype=np.float32)
cur_dir = os.path.dirname(os.path.abspath(__file__))


def rm_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=False, onerror=None)


def test_numpy_indexer():
    with NumpyIndexer(index_filename='np.test.gz') as indexer:
        indexer.add(vec_idx, vec)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        index_abspath = indexer.index_abspath
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
        assert idx.shape == (10, 4)

    rm_files([index_abspath, save_abspath])


def test_numpy_indexer_known():
    vectors = np.array([[1, 1, 1],
                        [10, 10, 10],
                        [100, 100, 100],
                        [1000, 1000, 1000]])
    keys = np.array([4, 5, 6, 7]).reshape(-1, 1)
    with NumpyIndexer(index_filename='np.test.gz') as indexer:
        indexer.add(keys, vectors)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        index_abspath = indexer.index_abspath
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

    rm_files([index_abspath, save_abspath])


def test_scipy_indexer():
    with NumpyIndexer(index_filename='np.test.gz', backend='scipy') as indexer:
        indexer.add(vec_idx, vec)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        index_abspath = indexer.index_abspath
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
        assert idx.shape == (10, 4)

    rm_files([index_abspath, save_abspath])
