import os
import unittest

import numpy as np
from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector.nmslib import NmslibIndexer
from tests import JinaTestCase

# fix the seed here
np.random.seed(500)
retr_idx = None
vec_idx = np.random.randint(0, high=100, size=[10])
vec = np.random.random([10, 10])
query = np.array(np.random.random([10, 10]), dtype=np.float32)
cur_dir = os.path.dirname(os.path.abspath(__file__))


class MyTestCase(JinaTestCase):

    def test_nmslib_indexer(self):
        with NmslibIndexer(index_filename='np.test.gz', space='l2') as a:
            a.add(vec_idx, vec)
            a.save()
            self.assertTrue(os.path.exists(a.index_abspath))
            index_abspath = a.index_abspath
            save_abspath = a.save_abspath
            # a.query(np.array(np.random.random([10, 5]), dtype=np.float32), top_k=4)

        with BaseIndexer.load(a.save_abspath) as b:
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
