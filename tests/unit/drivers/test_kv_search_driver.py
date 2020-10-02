from typing import Optional
import numpy as np

from jina.drivers.search import KVSearchDriver
from jina.drivers.helper import array2pb, pb2array
from jina.executors.indexers import BaseKVIndexer
from jina.proto import jina_pb2


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
        doc1.id = '1'
        doc1.embedding.CopyFrom(array2pb(np.array([int(doc1.id)])))
        doc2 = jina_pb2.Document()
        doc2.id = '2'
        doc2.embedding.CopyFrom(array2pb(np.array([int(doc2.id)])))
        doc3 = jina_pb2.Document()
        doc3.id = '3'
        doc3.embedding.CopyFrom(array2pb(np.array([int(doc3.id)])))
        doc4 = jina_pb2.Document()
        doc4.id = '4'
        doc4.embedding.CopyFrom(array2pb(np.array([int(doc4.id)])))
        self.db = {
            '1': doc1,
            '2': doc2,
            '3': doc3,
            '4': doc4
        }


class SimpleKVSearchDriver(KVSearchDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


def create_document_to_search():
    # 1-D embedding
    # doc: 0
    #   - chunk: 1
    #   - chunk: 2
    #   - chunk: 3
    #   - chunk: 4
    #   - chunk: 5 - will be missing from KV indexer
    doc = jina_pb2.Document()
    doc.granularity = 0
    doc.id = '0'
    for c in range(5):
        chunk = doc.chunks.add()
        chunk.granularity = doc.granularity + 1
        chunk.id = str(c + 1)
    return doc


def create_document_to_search_with_matches_on_chunks():
    # 1-D embedding
    # doc: 0
    #   - chunk: 1
    #     - match: 2
    #     - match: 3
    #     - match: 4
    #     - match: 5 - will be missing from KV indexer
    #     - match: 6 - will be missing from KV indexer
    doc = jina_pb2.Document()
    doc.id = '0'
    doc.granularity = 0
    chunk = doc.chunks.add()
    chunk.id = '1'
    chunk.granularity = doc.granularity + 1
    for m in range(5):
        match = chunk.matches.add()
        match.id = str(m + 2)
    return doc


def test_vectorsearch_driver_mock_indexer_apply_all():
    doc = create_document_to_search()
    driver = SimpleKVSearchDriver()

    executor = MockIndexer()
    driver.attach(executor=executor, pea=None)

    assert len(doc.chunks) == 5
    for chunk in doc.chunks:
        assert chunk.embedding.buffer == b''

    driver._apply_all(doc.chunks)

    # chunk idx: 5 had no matched and is removed as missing idx
    assert len(doc.chunks) == 4
    for chunk in doc.chunks:
        assert chunk.embedding.buffer != b''
        embedding_array = pb2array(chunk.embedding)
        np.testing.assert_equal(embedding_array, np.array([int(chunk.id)]))


def test_vectorsearch_driver_mock_indexer_traverse_apply():
    doc = create_document_to_search()
    driver = SimpleKVSearchDriver()

    executor = MockIndexer()
    driver.attach(executor=executor, pea=None)

    assert len(doc.chunks) == 5
    for chunk in doc.chunks:
        assert chunk.embedding.buffer == b''

    driver._traverse_apply(doc.chunks)

    # chunk idx: 5 had no matched and is removed as missing idx
    assert len(doc.chunks) == 4
    for chunk in doc.chunks:
        assert chunk.embedding.buffer != b''
        embedding_array = pb2array(chunk.embedding)
        np.testing.assert_equal(embedding_array, np.array([int(chunk.id)]))


def test_vectorsearch_driver_mock_indexer_with_matches_on_chunks():
    driver = SimpleKVSearchDriver(traversal_paths=('cm',))
    executor = MockIndexer()
    driver.attach(executor=executor, pea=None)
    doc = create_document_to_search_with_matches_on_chunks()

    driver._traverse_apply([doc])

    assert len(doc.chunks) == 1
    chunk = doc.chunks[0]
    assert len(chunk.matches) == 3
    for match in chunk.matches:
        assert match.embedding.buffer != b''
        embedding_array = pb2array(match.embedding)
        np.testing.assert_equal(embedding_array, np.array([int(match.id)]))

