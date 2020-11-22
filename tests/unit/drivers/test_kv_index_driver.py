from typing import Optional, Iterator

import pytest

from jina.drivers.index import KVIndexDriver
from jina.executors.indexers import BaseKVIndexer
from jina.proto import jina_pb2
from jina.types.document import uid, Document


class MockGroundTruthIndexer(BaseKVIndexer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs = {}

    def add(self, keys: Iterator[int], values: Iterator[bytes], *args, **kwargs):
        for key, value in zip(keys, values):
            self.docs[key] = value

    def query(self, key: int) -> Optional['jina_pb2.DocumentProto']:
        pass

    def get_query_handler(self):
        pass

    def get_add_handler(self):
        pass

    def get_create_handler(self):
        pass


class SimpleKVIndexDriver(KVIndexDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.fixture(scope='function')
def simple_kv_indexer_driver():
    return SimpleKVIndexDriver()


@pytest.fixture(scope='function')
def mock_groundtruth_indexer():
    return MockGroundTruthIndexer()


@pytest.fixture(scope='function')
def documents():
    docs = []
    # doc: 1
    # doc: 2
    # doc: 3
    # doc: 4
    # doc: 5
    for idx in range(5):
        with Document(text=str(idx+1)) as d:
            docs.append(d)

    return docs


def test_kv_index_driver(mock_groundtruth_indexer, simple_kv_indexer_driver, documents):
    simple_kv_indexer_driver.attach(executor=mock_groundtruth_indexer, pea=None)
    simple_kv_indexer_driver._apply_all(documents)

    assert len(mock_groundtruth_indexer.docs) == 5
    for idx, doc in enumerate(documents):
        assert mock_groundtruth_indexer.docs[uid.id2hash(doc.id)] == doc.SerializeToString()
