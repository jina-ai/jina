import os
import unittest
import numpy as np
from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector.ngt import NGTIndexer
from tests import JinaTestCase
import sys

PY37 = 'py37'
PY38 = 'py38'
py_tag = None
if sys.version_info >= (3, 8, 0):
    py_tag = PY38
elif sys.version_info >= (3, 7, 0):
    py_tag = PY37
else:
    raise OSError('Jina requires Python 3.7 and above, but yours is %s' % sys.version)

# fix the seed here
np.random.seed(500)
retr_idx = None
vec_idx = np.random.randint(0, high=100, size=[1, 10])
vec = np.random.random([10, 10])
query = np.array(np.random.random([10, 10]), dtype=np.float32)


@unittest.skipIf('py38' == py_tag, 'skip if python3.8 version is tested')
class MyTestCase(JinaTestCase):

    def test_simple_ngt(self):
        import ngtpy
        path = '/tmp/ngt-index'
        dimension, queries, top_k, batch_size, num_batch = 10, 3, 5, 8, 3

        ngtpy.create(path=path, dimension=dimension, distance_type='L2')
        _index = ngtpy.Index(path=path)
        for i in range(num_batch):
            _index.batch_insert(np.random.random((batch_size, dimension)), num_threads=4)
        self.assertTrue(os.path.exists(path))

        idx = []
        dist = []
        for key in np.random.random((queries, dimension)):
            results = _index.search(key, size=top_k, epsilon=0.1)
            index_k = []
            distance_k = []
            [(index_k.append(result[0]), distance_k.append(result[1])) for result in results]
            idx.append(index_k)
            dist.append(distance_k)

        idx = np.array(idx)
        dist = np.array(dist)

        self.assertEqual(idx.shape, dist.shape)
        self.assertEqual(idx.shape, (queries, top_k))

    def test_ngt_indexer(self):
        with NGTIndexer(index_filename='ngt.test.gz') as a:
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
