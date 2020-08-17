import os

from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector.milvus import MilvusIndexer
from tests import JinaTestCase


class MilvusTestCase(JinaTestCase):

    def test_milvus_indexer_save_and_load(self):
        with MilvusIndexer('localhost', 19530,
                           'collection', 'IVF', {'key': 'value'}) as indexer:
            indexer.touch()
            indexer.save()
            self.assertTrue(os.path.exists(indexer.save_abspath))
            save_abspath = indexer.save_abspath

        with BaseIndexer.load(save_abspath) as indexer:
            self.assertIsInstance(indexer, MilvusIndexer)
            self.assertEqual(indexer.host, 'localhost')
            self.assertEqual(indexer.port, 19530)
            self.assertEqual(indexer.collection_name, 'collection')
            self.assertEqual(indexer.index_type, 'IVF')
            self.assertEqual(indexer.index_params['key'], 'value')

        self.add_tmpfile(save_abspath)
