import os
import unittest

import numpy as np
from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector.annoy import AnnoyIndexer
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

    def test_annoy_wrap_indexer(self):
        with NumpyIndexer(index_filename='wrap-npidx.gz') as a:
            a.name = 'wrap-npidx'
            a.add(vec_idx, vec)
            a.save()
            index_abspath = a.index_abspath
            save_abspath = a.save_abspath

        with BaseIndexer.load_config(os.path.join(cur_dir, 'annoy-wrap.yml')) as b:
            idx, dist = b.query(query, top_k=4)
            global retr_idx
            if retr_idx is None:
                retr_idx = idx
            else:
                np.testing.assert_almost_equal(retr_idx, idx)
            self.assertEqual(idx.shape, dist.shape)
            self.assertEqual(idx.shape, (10, 4))

        with BaseIndexer.load_config(os.path.join(cur_dir, 'nmslib-wrap.yml')) as c:
            idx, dist = c.query(query, top_k=4)
            if retr_idx is None:
                retr_idx = idx
            else:
                np.testing.assert_almost_equal(retr_idx, idx)
            self.assertEqual(idx.shape, dist.shape)
            self.assertEqual(idx.shape, (10, 4))
            self.add_tmpfile(index_abspath, save_abspath)

    def test_simple_annoy(self):
        from annoy import AnnoyIndex
        _index = AnnoyIndex(5, 'angular')
        for j in range(3):
            _index.add_item(j, np.random.random((5,)))
        _index.build(4)
        idx1, _ = _index.get_nns_by_vector(np.random.random((5,)), 3, include_distances=True)

    def test_annoy_indexer(self):
        with AnnoyIndexer(index_filename='annoy.test.gz') as a:
            a.add(vec_idx, vec)
            a.save()
            self.assertTrue(os.path.exists(a.index_abspath))
            index_abspath = a.index_abspath
            save_abspath = a.save_abspath

        with BaseIndexer.load(save_abspath) as b:
            idx, dist = b.query(query, top_k=4)
            print(idx, dist)
            global retr_idx
            if retr_idx is None:
                retr_idx = idx
            else:
                np.testing.assert_almost_equal(retr_idx, idx)
            self.assertEqual(idx.shape, dist.shape)
            self.assertEqual(idx.shape, (10, 4))

        self.add_tmpfile(index_abspath, save_abspath)

    def test_annoy_indexer_with_no_search_k(self):
        with AnnoyIndexer(index_filename='annoy.test.gz', search_k=0) as a:
            a.add(vec_idx, vec)
            a.save()
            self.assertTrue(os.path.exists(a.index_abspath))
            index_abspath = a.index_abspath
            save_abspath = a.save_abspath

        with BaseIndexer.load(save_abspath) as b:
            idx, dist = b.query(query, top_k=4)
            # search_k is 0, so no tree is searched for
            self.assertEqual(idx.shape, dist.shape)
            self.assertEqual(idx.shape, (10, 0))

        self.add_tmpfile(index_abspath, save_abspath)


if __name__ == '__main__':
    unittest.main()