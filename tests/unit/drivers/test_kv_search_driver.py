from typing import Optional

import numpy as np

from jina import Document
from jina.drivers.search import KVSearchDriver
from jina.executors.indexers import BaseKVIndexer
from jina.proto import jina_pb2
from jina.types.document.uid import id2hash
from jina.types.ndarray.generic import NdArray


class MockIndexer(BaseKVIndexer):

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        pass

    def query(self, key: int) -> Optional['jina_pb2.DocumentProto']:
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
        doc1 = Document()
        doc1.id = str(1) * 16
        doc1.embedding = np.array([int(doc1.id)])
        doc2 = Document()
        doc2.id = str(2) * 16
        doc2.embedding = np.array([int(doc2.id)])
        doc3 = Document()
        doc3.id = str(3) * 16
        doc3.embedding = np.array([int(doc3.id)])
        doc4 = Document()
        doc4.id = str(4) * 16
        doc4.embedding = np.array([int(doc4.id)])
        self.db = {
            id2hash(doc1.id): doc1.SerializeToString(),
            id2hash(doc2.id): doc2.SerializeToString(),
            id2hash(doc3.id): doc3.SerializeToString(),
            id2hash(doc4.id): doc4.SerializeToString()
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
    doc = Document()
    doc.id = '0' * 16
    for c in range(5):
        chunk = doc.chunks.new()
        chunk.id = str(c + 1) * 16
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
    doc = Document()
    doc.id = '0' * 16
    chunk = doc.chunks.new()
    chunk.id = '1' * 16
    for m in range(5):
        d = Document(id=str(m + 2) * 16)
        d.score.value = 1.
        chunk.matches.append(d)
    return doc


def test_vectorsearch_driver_mock_indexer_apply_all():
    doc = create_document_to_search()
    driver = SimpleKVSearchDriver()

    executor = MockIndexer()
    driver.attach(executor=executor, pea=None)

    dcs = list(doc.chunks)
    assert len(dcs) == 5
    for chunk in dcs:
        assert chunk.embedding is None

    driver._apply_all(doc.chunks)

    dcs = list(doc.chunks)

    # chunk idx: 5 had no matched and is removed as missing idx
    assert len(dcs) == 4
    for chunk in dcs:
        assert chunk.embedding is not None
        embedding_array = chunk.embedding
        np.testing.assert_equal(embedding_array, np.array([int(chunk.id)]))


def test_vectorsearch_driver_mock_indexer_traverse_apply():
    doc = create_document_to_search()
    driver = SimpleKVSearchDriver()

    executor = MockIndexer()
    driver.attach(executor=executor, pea=None)

    dcs = list(doc.chunks)
    assert len(dcs) == 5
    for chunk in dcs:
        assert chunk.embedding is None

    driver._traverse_apply(doc.chunks)

    # chunk idx: 5 had no matched and is removed as missing idx
    dcs = list(doc.chunks)
    assert len(dcs) == 4
    for chunk in dcs:
        assert chunk.embedding is not None
        embedding_array = chunk.embedding
        np.testing.assert_equal(embedding_array, np.array([int(chunk.id)]))


def test_vectorsearch_driver_mock_indexer_with_matches_on_chunks():
    driver = SimpleKVSearchDriver(traversal_paths=('cm',))
    executor = MockIndexer()
    driver.attach(executor=executor, pea=None)
    doc = create_document_to_search_with_matches_on_chunks()

    driver._traverse_apply([doc])

    dcs = list(doc.chunks)
    assert len(dcs) == 1
    chunk = dcs[0]
    matches = list(chunk.matches)
    assert len(matches) == 3
    for match in matches:
        assert NdArray(match.embedding).value is not None
        embedding_array = NdArray(match.embedding).value
        np.testing.assert_equal(embedding_array, np.array([int(match.id)]))
