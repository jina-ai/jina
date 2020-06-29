import os
import unittest

import numpy as np
from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector.annoy import AnnoyIndexer
from jina.executors.indexers.vector.nmslib import NmslibIndexer
from jina.executors.indexers.vector.numpy import NumpyIndexer
from tests import JinaTestCase

# fix the seed here
np.random.seed(500)
retr_idx = None
vec_idx = np.random.randint(0, high=100, size=[10])
vec = np.random.random([10, 10])
query = np.array(np.random.random([10, 10]), dtype=np.float32)


class MyTestCase(JinaTestCase):

    def test_annoy_wrap_indexer(self):
        a = NumpyIndexer(index_filename='wrap-npidx.gz')
        a.name = 'wrap-npidx'
        a.add(vec_idx, vec)
        a.save()
        a.close()

        b = BaseIndexer.load_config('annoy-wrap.yml')
        idx, dist = b.query(query, top_k=4)
        print(idx, dist)
        global retr_idx
        if retr_idx is None:
            retr_idx = idx
        else:
            np.testing.assert_almost_equal(retr_idx, idx)
        self.assertEqual(idx.shape, dist.shape)
        self.assertEqual(idx.shape, (10, 4))

        c = BaseIndexer.load_config('nmslib-wrap.yml')
        idx, dist = c.query(query, top_k=4)
        print(idx, dist)
        if retr_idx is None:
            retr_idx = idx
        else:
            np.testing.assert_almost_equal(retr_idx, idx)
        self.assertEqual(idx.shape, dist.shape)
        self.assertEqual(idx.shape, (10, 4))
        self.add_tmpfile(a.index_abspath, a.save_abspath)

    def test_simple_annoy(self):
        from annoy import AnnoyIndex
        _index = AnnoyIndex(5, 'angular')
        for j in range(3):
            _index.add_item(j, np.random.random((5,)))
        _index.build(4)
        idx1, _ = _index.get_nns_by_vector(np.random.random((5,)), 3, include_distances=True)

    def test_np_indexer(self):
        a = NumpyIndexer(index_filename='np.test.gz')
        a.add(vec_idx, vec)
        a.save()
        a.close()
        self.assertTrue(os.path.exists(a.index_abspath))
        # a.query(np.array(np.random.random([10, 5]), dtype=np.float32), top_k=4)

        b = BaseIndexer.load(a.save_abspath)
        idx, dist = b.query(query, top_k=4)
        print(idx, dist)
        global retr_idx
        if retr_idx is None:
            retr_idx = idx
        else:
            np.testing.assert_almost_equal(retr_idx, idx)
        self.assertEqual(idx.shape, dist.shape)
        self.assertEqual(idx.shape, (10, 4))
        self.add_tmpfile(a.index_abspath, a.save_abspath)

    def test_scipy_indexer(self):
        a = NumpyIndexer(index_filename='np.test.gz', backend='scipy')
        a.add(vec_idx, vec)
        a.save()
        a.close()
        self.assertTrue(os.path.exists(a.index_abspath))
        # a.query(np.array(np.random.random([10, 5]), dtype=np.float32), top_k=4)

        b = BaseIndexer.load(a.save_abspath)
        idx, dist = b.query(query, top_k=4)
        print(idx, dist)
        global retr_idx
        if retr_idx is None:
            retr_idx = idx
        else:
            np.testing.assert_almost_equal(retr_idx, idx)
        self.assertEqual(idx.shape, dist.shape)
        self.assertEqual(idx.shape, (10, 4))
        self.add_tmpfile(a.index_abspath, a.save_abspath)

    def test_nmslib_indexer(self):
        a = NmslibIndexer(index_filename='np.test.gz', space='l2')
        a.add(vec_idx, vec)
        a.save()
        a.close()
        self.assertTrue(os.path.exists(a.index_abspath))
        # a.query(np.array(np.random.random([10, 5]), dtype=np.float32), top_k=4)

        b = BaseIndexer.load(a.save_abspath)
        idx, dist = b.query(query, top_k=4)
        print(idx, dist)
        global retr_idx
        if retr_idx is None:
            retr_idx = idx
        else:
            np.testing.assert_almost_equal(retr_idx, idx)
        self.assertEqual(idx.shape, dist.shape)
        self.assertEqual(idx.shape, (10, 4))
        self.add_tmpfile(a.index_abspath, a.save_abspath)

    def test_annoy_indexer(self):
        a = AnnoyIndexer(index_filename='annoy.test.gz')
        a.add(vec_idx, vec)
        a.save()
        a.close()
        self.assertTrue(os.path.exists(a.index_abspath))
        # a.query(np.array(np.random.random([10, 5]), dtype=np.float32), top_k=4)

        b = BaseIndexer.load(a.save_abspath)
        idx, dist = b.query(query, top_k=4)
        print(idx, dist)
        global retr_idx
        if retr_idx is None:
            retr_idx = idx
        else:
            np.testing.assert_almost_equal(retr_idx, idx)
        self.assertEqual(idx.shape, dist.shape)
        self.assertEqual(idx.shape, (10, 4))
        self.add_tmpfile(a.index_abspath, a.save_abspath)


if __name__ == '__main__':
    unittest.main()
