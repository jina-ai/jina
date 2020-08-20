import os

import numpy as np
from jina.executors.indexers import BaseIndexer
from jina.hub.indexers.vector.annoy import AnnoyIndexer
from jina.hub.indexers.vector.numpy import NumpyIndexer
from tests import JinaTestCase

# fix the seed here
np.random.seed(500)
retr_idx = None
vec_idx = np.random.randint(0, high=100, size=[10])
vec = np.random.random([10, 10])
query = np.array(np.random.random([10, 10]), dtype=np.float32)
cur_dir = os.path.dirname(os.path.abspath(__file__))


class AnnoyIndexerTestCase(JinaTestCase):

    def test_annoy_wrap_indexer(self):
        with NumpyIndexer(index_filename='wrap-npidx.gz') as indexer:
            indexer.name = 'wrap-npidx'
            indexer.add(vec_idx, vec)
            indexer.save()
            index_abspath = indexer.index_abspath
            save_abspath = indexer.save_abspath
            self.add_tmpfile(index_abspath, save_abspath)

        with BaseIndexer.load_config(os.path.join(cur_dir, 'yaml/annoy-wrap.yml')) as indexer:
            self.assertIsInstance(indexer, AnnoyIndexer)
            idx, dist = indexer.query(query, top_k=4)
            global retr_idx
            if retr_idx is None:
                retr_idx = idx
            else:
                np.testing.assert_almost_equal(retr_idx, idx)
            assert idx.shape == dist.shape
            assert idx.shape == (10, 4)

    def test_simple_annoy(self):
        from annoy import AnnoyIndex
        _index = AnnoyIndex(5, 'angular')
        for j in range(3):
            _index.add_item(j, np.random.random((5,)))
        _index.build(4)
        idx1, _ = _index.get_nns_by_vector(np.random.random((5,)), 3, include_distances=True)
        assert len(idx1) == 3

    def test_annoy_indexer(self):
        with AnnoyIndexer(index_filename='annoy.test.gz') as indexer:
            indexer.add(vec_idx, vec)
            indexer.save()
            self.assertTrue(os.path.exists(indexer.index_abspath))
            index_abspath = indexer.index_abspath
            save_abspath = indexer.save_abspath

        with BaseIndexer.load(save_abspath) as indexer:
            self.assertIsInstance(indexer, AnnoyIndexer)
            idx, dist = indexer.query(query, top_k=4)
            global retr_idx
            if retr_idx is None:
                retr_idx = idx
            else:
                np.testing.assert_almost_equal(retr_idx, idx)
            assert idx.shape == dist.shape
            assert idx.shape == (10, 4)

        self.add_tmpfile(index_abspath, save_abspath)

    def test_annoy_indexer_with_no_search_k(self):
        with AnnoyIndexer(index_filename='annoy.test.gz', search_k=0) as indexer:
            indexer.add(vec_idx, vec)
            indexer.save()
            self.assertTrue(os.path.exists(indexer.index_abspath))
            index_abspath = indexer.index_abspath
            save_abspath = indexer.save_abspath

        with BaseIndexer.load(save_abspath) as indexer:
            self.assertIsInstance(indexer, AnnoyIndexer)
            idx, dist = indexer.query(query, top_k=4)
            # search_k is 0, so no tree is searched for
            assert idx.shape == dist.shape
            assert idx.shape == (10, 0)

        self.add_tmpfile(index_abspath, save_abspath)
