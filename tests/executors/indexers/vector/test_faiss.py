import os
import unittest
import gzip

import numpy as np
from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector.faiss import FaissIndexer
from tests import JinaTestCase

# fix the seed here
np.random.seed(500)
retr_idx = None
vec_idx = np.random.randint(0, high=100, size=[10])
vec = np.array(np.random.random([10, 10]), dtype=np.float32)
query = np.array(np.random.random([10, 10]), dtype=np.float32)
cur_dir = os.path.dirname(os.path.abspath(__file__))


class MyTestCase(JinaTestCase):

    @unittest.skip
    def test_faiss_indexer(self):
        train_filepath = os.path.join(cur_dir, 'train.tgz')
        train_data = np.array(np.random.random([1024, 10]), dtype=np.float32)
        with gzip.open(train_filepath, 'wb', compresslevel=1) as f:
            f.write(train_data.tobytes())

        with FaissIndexer(index_filename='faiss.test.gz', index_key='IVF10,PQ2', train_filepath=train_filepath) as a:
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

        self.add_tmpfile(index_abspath, save_abspath, train_filepath)


if __name__ == '__main__':
    unittest.main()
