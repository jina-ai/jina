from typing import Optional

import numpy as np
import pytest

from jina import Document
from jina.drivers.search import KVSearchDriver
from jina.executors.indexers import BaseKVIndexer
from jina.proto import jina_pb2
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
        self.db = {}
        doc_ids = ['1', '2', '3', '4']
        doc_ids = [item * 16 for item in doc_ids]
        for doc_id in doc_ids:
            with Document() as doc:
                doc.id = doc_id
                doc.embedding = np.array([int(doc.id)])
            self.db[int(doc.id)] = doc.SerializeToString()



class SimpleKVSearchDriver(KVSearchDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.fixture(scope='function')
def document():
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
        with Document() as chunk:
            chunk.id = str(c + 1) * 16
        doc.chunks.add(chunk)
    return doc


@pytest.fixture(scope='function')
def document_with_matches_on_chunks():
    # 1-D embedding
    # doc: 0
    #   - chunk: 1
    #     - match: 2
    #     - match: 3
    #     - match: 4
    #     - match: 5 - will be missing from KV indexer
    #     - match: 6 - will be missing from KV indexer
    with Document() as doc:
        doc.id = '0' * 16
        with Document() as chunk:
            chunk.id = '1' * 16
            for m in range(5):
                with Document() as match:
                    match.id = str(m + 2) * 16
                    match.score.value = 1.
                chunk.matches.append(match)
        doc.chunks.append(chunk)
    return doc


def test_vectorsearch_driver_mock_indexer_apply_all(document):
    driver = SimpleKVSearchDriver()

    executor = MockIndexer()
    driver.attach(executor=executor, runtime=None)

    dcs = list(document.chunks)
    assert len(dcs) == 5
    for chunk in dcs:
        assert chunk.embedding is None

    driver._apply_all(document.chunks)

    dcs = list(document.chunks)

    # chunk idx: 5 had no matched and is removed as missing idx
    assert len(dcs) == 4
    for chunk in dcs:
        assert chunk.embedding is not None
        embedding_array = chunk.embedding
        np.testing.assert_equal(embedding_array, np.array([int(chunk.id)]))


def test_vectorsearch_driver_mock_indexer_traverse_apply(document):
    driver = SimpleKVSearchDriver()

    executor = MockIndexer()
    driver.attach(executor=executor, runtime=None)

    dcs = list(document.chunks)
    assert len(dcs) == 5
    for chunk in dcs:
        assert chunk.embedding is None

    driver._traverse_apply(document.chunks)

    # chunk idx: 5 had no matched and is removed as missing idx
    dcs = list(document.chunks)
    assert len(dcs) == 4
    for chunk in dcs:
        assert chunk.embedding is not None
        embedding_array = chunk.embedding
        np.testing.assert_equal(embedding_array, np.array([int(chunk.id)]))


def test_vectorsearch_driver_mock_indexer_with_matches_on_chunks(document_with_matches_on_chunks):
    driver = SimpleKVSearchDriver(traversal_paths=('cm',))
    executor = MockIndexer()
    driver.attach(executor=executor, runtime=None)

    driver._traverse_apply([document_with_matches_on_chunks])

    dcs = list(document_with_matches_on_chunks.chunks)
    assert len(dcs) == 1
    chunk = dcs[0]
    matches = list(chunk.matches)
    assert len(matches) == 3
    for match in matches:
        assert NdArray(match.embedding).value is not None
        embedding_array = NdArray(match.embedding).value
        np.testing.assert_equal(embedding_array, np.array([int(match.id)]))
