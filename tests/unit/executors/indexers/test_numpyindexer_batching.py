import os

import pytest
import numpy as np

from jina.executors.decorators import batching
from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector import NumpyIndexer, _ext_B, _euclidean


class MockNumpyIndexer(NumpyIndexer):

    @batching(merge_over_axis=1, slice_on=2)
    def _euclidean(self, cached_A, raw_B):
        assert raw_B.shape[0] == self.batch_size
        data = _ext_B(raw_B)
        return _euclidean(cached_A, data)


@pytest.mark.parametrize('batch_size', [2, 5, 10, 20, 100, 500])
def test_numpy_indexer_known_big_batch(batch_size, test_metas):
    """Let's try to have some real test. We will have an index with 10k vectors of random values between 5 and 10.
     We will change tweak some specific vectors that we expect to be retrieved at query time. We will tweak vector
     at index [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000], this will also be the query vectors.
     Then the keys will be assigned shifted to test the proper usage of `int2ext_id` and `ext2int_id`
    """
    vectors = np.random.uniform(low=5.0, high=10.0, size=(10000, 1024))

    queries = np.empty((10, 1024))
    for idx in range(0, 10000, 1000):
        array = idx * np.ones((1, 1024))
        queries[int(idx / 1000)] = array
        vectors[idx] = array

    keys = np.arange(10000, 20000).reshape(-1, 1)

    with MockNumpyIndexer(metric='euclidean', index_filename='np.test.gz', compress_level=0,
                          metas=test_metas) as indexer:
        indexer.batch_size = batch_size
        indexer.add(keys, vectors)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        indexer.batch_size = batch_size
        assert isinstance(indexer, MockNumpyIndexer)
        assert isinstance(indexer.raw_ndarray, np.memmap)
        idx, dist = indexer.query(queries, top_k=1)
        np.testing.assert_equal(idx, np.array(
            [[10000], [11000], [12000], [13000], [14000], [15000], [16000], [17000], [18000], [19000]]))
        assert idx.shape == dist.shape
        assert idx.shape == (10, 1)
        np.testing.assert_equal(indexer.query_by_id([10000, 15000]), vectors[[0, 5000]])
