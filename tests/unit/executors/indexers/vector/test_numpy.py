import os
import unittest

import numpy as np
from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector.numpy import NumpyIndexer
from tests import JinaTestCase

# fix the seed here
np.random.seed(500)
retr_idx = None
vec_idx = np.random.randint(0, high=100, size=[10])
vec = np.random.random([10, 10])
query = np.array(np.random.random([10, 10]), dtype=np.float32)
cur_dir = os.path.dirname(os.path.abspath(__file__))


class MyTestCase(JinaTestCase):

    def test_np_indexer(self):
        with NumpyIndexer(index_filename='np.test.gz') as a:
            a.add(vec_idx, vec)
            a.save()
            self.assertTrue(os.path.exists(a.index_abspath))
            index_abspath = a.index_abspath
            save_abspath = a.save_abspath

        with BaseIndexer.load(save_abspath) as b:
            idx, dist = b.query(query, top_k=4)
            global retr_idx
            if retr_idx is None:
                retr_idx = idx
            else:
                np.testing.assert_almost_equal(retr_idx, idx)
            self.assertEqual(idx.shape, dist.shape)
            self.assertEqual(idx.shape, (10, 4))

        self.add_tmpfile(index_abspath, save_abspath)

    def test_np_indexer_known(self):
        vectors = np.array([[1, 1, 1],
                            [10, 10, 10],
                            [100, 100, 100],
                            [1000, 1000, 1000]])
        keys = np.array([0, 1, 2, 3]).reshape(-1, 1)
        with NumpyIndexer(index_filename='np.test.gz') as a:
            a.add(keys, vectors)
            a.save()
            self.assertTrue(os.path.exists(a.index_abspath))
            index_abspath = a.index_abspath
            save_abspath = a.save_abspath

        queries = np.array([[1, 1, 1],
                            [10, 10, 10],
                            [100, 100, 100],
                            [1000, 1000, 1000]])
        with BaseIndexer.load(save_abspath) as b:
            idx, dist = b.query(queries, top_k=2)
            np.testing.assert_equal(idx, np.array([[0, 1], [1, 0], [2, 1], [3, 2]]))
            self.assertEqual(idx.shape, dist.shape)
            self.assertEqual(idx.shape, (4, 2))

        self.add_tmpfile(index_abspath, save_abspath)

    def test_scipy_indexer(self):
        with NumpyIndexer(index_filename='np.test.gz', backend='scipy') as a:
            a.add(vec_idx, vec)
            a.save()
            self.assertTrue(os.path.exists(a.index_abspath))
            index_abspath = a.index_abspath
            save_abspath = a.save_abspath

        with BaseIndexer.load(save_abspath) as b:
            idx, dist = b.query(query, top_k=4)
            global retr_idx
            if retr_idx is None:
                retr_idx = idx
            else:
                np.testing.assert_almost_equal(retr_idx, idx)
            self.assertEqual(idx.shape, dist.shape)
            self.assertEqual(idx.shape, (10, 4))

        self.add_tmpfile(index_abspath, save_abspath)


if __name__ == '__main__':
    unittest.main()
