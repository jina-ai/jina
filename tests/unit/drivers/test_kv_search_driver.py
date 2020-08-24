from typing import Optional
import numpy as np

from jina.drivers.search import KVSearchDriver
from jina.drivers.helper import array2pb, pb2array
from jina.executors.indexers import BaseKVIndexer
from jina.proto import jina_pb2
from tests import JinaTestCase


class MockIndexer(BaseKVIndexer):

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        pass

    def query(self, key: int) -> Optional['jina_pb2.Document']:
        if key in self.db.keys():
            return self.db[key]
        else:
            return None

    def get_query_handler(self):
        pass

    def get_add_handler(self):
        pass

    def get_create_handler(self):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        doc1 = jina_pb2.Document()
        doc1.id = 1
        doc1.embedding.CopyFrom(array2pb(np.array([doc1.id])))
        doc2 = jina_pb2.Document()
        doc2.id = 2
        doc2.embedding.CopyFrom(array2pb(np.array([doc2.id])))
        doc3 = jina_pb2.Document()
        doc3.id = 3
        doc3.embedding.CopyFrom(array2pb(np.array([doc3.id])))
        doc4 = jina_pb2.Document()
        doc4.id = 4
        doc4.embedding.CopyFrom(array2pb(np.array([doc4.id])))
        self.db = {
            1: doc1,
            2: doc2,
            3: doc3,
            4: doc4
        }


class SimpleKVSearchDriver(KVSearchDriver):

    def __init__(self, top_k,  *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


def create_document_to_search():
    # 1-D embedding
    # doc: 0 - chunk: 1
    #        - chunk: 2
    #        - chunk: 3
    #        - chunk: 4
    #        - chunk: 5 - will be missing from KV indexer
    # ....
    doc = jina_pb2.Document()
    doc.id = 0
    for c in range(5):
        chunk = doc.chunks.add()
        chunk.id = c + 1
    return doc


class VectorSearchDriverTestCase(JinaTestCase):

    def test_vectorsearch_driver_mock_indexer(self):
        doc = create_document_to_search()
        driver = SimpleKVSearchDriver(top_k=2)
        executor = MockIndexer()
        driver.attach(executor=executor, pea=None)

        assert len(doc.chunks) == 5
        for chunk in doc.chunks:
            assert chunk.embedding.buffer == b''

        driver._apply_all(doc.chunks)

        # chunk idx: 5 had no matched and is removed as missing idx
        assert len(doc.chunks) == 4
        for chunk in doc.chunks:
            self.assertNotEqual(chunk.embedding.buffer, b'')
            embedding_array = pb2array(chunk.embedding)
            np.testing.assert_equal(embedding_array, np.array([chunk.id]))

