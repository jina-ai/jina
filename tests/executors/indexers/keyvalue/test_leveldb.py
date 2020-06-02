import os
import unittest

import jina.proto.jina_pb2 as jina_pb2
from google.protobuf.json_format import MessageToJson
from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.keyvalue.leveldb import LeveldbIndexer
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def _create_Document(self, doc_id, text, weight, length):
        d = jina_pb2.Document()
        d.doc_id = doc_id
        d.buffer = text.encode('utf8')
        d.weight = weight
        d.length = length
        return d

    def run_test(self, indexer):
        data = {
            'd1': MessageToJson(self._create_Document(1, 'cat', 0.1, 3)),
            'd2': MessageToJson(self._create_Document(2, 'dog', 0.2, 3)),
            'd3': MessageToJson(self._create_Document(3, 'bird', 0.3, 3)),
        }
        indexer.add(data)
        indexer.save()
        indexer.close()
        self.assertTrue(os.path.exists(indexer.index_abspath))

        searcher = BaseIndexer.load(indexer.save_abspath)
        doc = searcher.query('d2')
        self.assertEqual(doc.doc_id, 2)
        self.assertEqual(doc.length, 3)
        self.add_tmpfile(indexer.save_abspath, indexer.index_abspath)

    def test_add_query(self):
        indexer = LeveldbIndexer(index_filename='leveldb.db')
        self.run_test(indexer)

    def test_load_yaml(self):
        from jina.executors import BaseExecutor
        indexer = BaseExecutor.load_config('../../../yaml/test-leveldb.yml')
        self.run_test(indexer)


if __name__ == '__main__':
    unittest.main()
