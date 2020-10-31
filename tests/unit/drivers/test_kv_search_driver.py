from typing import Optional

import numpy as np

from jina.drivers.search import KVSearchDriver
from jina.executors.indexers import BaseKVIndexer
from jina.proto import jina_pb2
from jina.proto.ndarray.generic import GenericNdArray


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
        GenericNdArray(doc1.embedding).value = np.array([int(doc1.id)])
        doc2 = jina_pb2.Document()
        doc2.id = '2'
        GenericNdArray(doc2.embedding).value = np.array([int(doc2.id)])
        doc3 = jina_pb2.Document()
        doc3.id = '3'
        GenericNdArray(doc3.embedding).value = np.array([int(doc3.id)])
        doc4 = jina_pb2.Document()
        doc4.id = '4'
        GenericNdArray(doc4.embedding).value = np.array([int(doc4.id)])
        self.db = {
            1: doc1.SerializeToString(),
            2: doc2.SerializeToString(),
            3: doc3.SerializeToString(),
            4: doc4.SerializeToString()
        }


class SimpleKVSearchDriver(KVSearchDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hash2id = lambda x: str(int(x))
        self.id2hash = lambda x: int(x)

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
        assert GenericNdArray(chunk.embedding).value is None

    driver._apply_all(doc.chunks)

    # chunk idx: 5 had no matched and is removed as missing idx
    assert len(doc.chunks) == 4
    for chunk in doc.chunks:
        assert GenericNdArray(chunk.embedding).value is not None
        embedding_array = GenericNdArray(chunk.embedding).value
        np.testing.assert_equal(embedding_array, np.array([int(chunk.id)]))


def test_vectorsearch_driver_mock_indexer_traverse_apply():
    doc = create_document_to_search()
    driver = SimpleKVSearchDriver()

    executor = MockIndexer()
    driver.attach(executor=executor, pea=None)

    assert len(doc.chunks) == 5
    for chunk in doc.chunks:
        assert GenericNdArray(chunk.embedding).value is None

    driver._traverse_apply(doc.chunks)

    # chunk idx: 5 had no matched and is removed as missing idx
    assert len(doc.chunks) == 4
    for chunk in doc.chunks:
        assert GenericNdArray(chunk.embedding).value is not None
        embedding_array = GenericNdArray(chunk.embedding).value
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
        assert GenericNdArray(match.embedding).value is not None
        embedding_array = GenericNdArray(match.embedding).value
        np.testing.assert_equal(embedding_array, np.array([int(match.id)]))
