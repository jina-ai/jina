import os

import numpy as np
from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector.numpy import NumpyIndexer
from jina.executors.indexers.vector.nmslib import NmslibIndexer
from tests import JinaTestCase

# fix the seed here
np.random.seed(500)
retr_idx = None
vec_idx = np.random.randint(0, high=100, size=[10])
vec = np.random.random([10, 10])
query = np.array(np.random.random([10, 10]), dtype=np.float32)
cur_dir = os.path.dirname(os.path.abspath(__file__))


class NmsLibTestCase(JinaTestCase):

    def test_nmslib_indexer(self):
        with NmslibIndexer(index_filename='np.test.gz', space='l2') as indexer:
            indexer.add(vec_idx, vec)
            indexer.save()
            self.assertTrue(os.path.exists(indexer.index_abspath))
            index_abspath = indexer.index_abspath
            save_abspath = indexer.save_abspath
            # a.query(np.array(np.random.random([10, 5]), dtype=np.float32), top_k=4)

        with BaseIndexer.load(indexer.save_abspath) as indexer:
            self.assertIsInstance(indexer, NmslibIndexer)
            idx, dist = indexer.query(query, top_k=4)
            global retr_idx
            if retr_idx is None:
                retr_idx = idx
            else:
                np.testing.assert_almost_equal(retr_idx, idx)
            self.assertEqual(idx.shape, dist.shape)
            self.assertEqual(idx.shape, (10, 4))

        self.add_tmpfile(index_abspath, save_abspath)

    def test_nmslib_wrap_indexer(self):
        with NumpyIndexer(index_filename='wrap-npidx.gz') as indexer:
            indexer.name = 'wrap-npidx'
            indexer.add(vec_idx, vec)
            indexer.save()
            index_abspath = indexer.index_abspath
            save_abspath = indexer.save_abspath
            self.add_tmpfile(index_abspath, save_abspath)

        with BaseIndexer.load_config(os.path.join(cur_dir, 'yaml/nmslib-wrap.yml')) as indexer:
            self.assertIsInstance(indexer, NmslibIndexer)
            idx, dist = indexer.query(query, top_k=4)
            global retr_idx
            if retr_idx is None:
                retr_idx = idx
            else:
                np.testing.assert_almost_equal(retr_idx, idx)
            self.assertEqual(idx.shape, dist.shape)
            self.assertEqual(idx.shape, (10, 4))
            self.add_tmpfile(index_abspath, save_abspath)
