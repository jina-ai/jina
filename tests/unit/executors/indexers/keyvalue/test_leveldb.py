import os
import unittest

import jina.proto.jina_pb2 as jina_pb2
from google.protobuf.json_format import MessageToJson
from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.keyvalue.leveldb import LeveldbIndexer
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


class MyTestCase(JinaTestCase):
    def _create_Document(self, doc_id, text, weight, length):
        d = jina_pb2.Document()
        d.doc_id = doc_id
        d.buffer = text.encode('utf8')
        d.weight = weight
        d.length = length
        return d

    def run_test(self, indexer):
        with indexer as idx:
            data = {
                'd1': MessageToJson(self._create_Document(1, 'cat', 0.1, 3)),
                'd2': MessageToJson(self._create_Document(2, 'dog', 0.2, 3)),
                'd3': MessageToJson(self._create_Document(3, 'bird', 0.3, 3)),
            }
            idx.add(data)
            idx.save()
            save_abspath = idx.save_abspath
            index_abspath = idx.index_abspath
        self.assertTrue(os.path.exists(index_abspath))

        with BaseIndexer.load(save_abspath) as searcher:
            doc = searcher.query('d2')
            self.assertEqual(doc.doc_id, 2)
            self.assertEqual(doc.length, 3)

        self.add_tmpfile(save_abspath, index_abspath)

    def test_add_query(self):
        indexer = LeveldbIndexer(level='doc', index_filename='leveldb.db')
        self.run_test(indexer)

    def test_load_yaml(self):
        from jina.executors import BaseExecutor
        indexer = BaseExecutor.load_config(os.path.join(cur_dir, '../../../yaml/test-leveldb.yml'))
        self.run_test(indexer)


if __name__ == '__main__':
    unittest.main()
