import pytest

from typing import Optional, Iterator
from jina.drivers.evaluate import GroundTruthKVIndexDriver
from jina.executors.indexers import BaseKVIndexer
from jina.proto import jina_pb2


class MockGroundTruthIndexer(BaseKVIndexer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs = {}

    def add(self, keys: Iterator[int], values: Iterator[bytes], *args, **kwargs):
        for key, value in zip(keys, values):
            self.docs[key] = value

    def query(self, key: int) -> Optional['jina_pb2.Document']:
        pass

    def get_query_handler(self):
        pass

    def get_add_handler(self):
        pass

    def get_create_handler(self):
        pass


class SimpleGroundTruthKVIndexDriver(GroundTruthKVIndexDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id_tag = 'id'

    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.fixture(scope='function')
def simple_kv_groundtruth_indexer_driver():
    return SimpleGroundTruthKVIndexDriver()


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
    # doc: 5 - will be missing from KV indexer
    for idx in range(5):
        doc = jina_pb2.Document()
        doc.tags['id'] = idx + 1
        docs.append(doc)

    return docs


def test_load_groundtruth_driver(mock_groundtruth_indexer, simple_kv_groundtruth_indexer_driver, documents):
    simple_kv_groundtruth_indexer_driver.attach(executor=mock_groundtruth_indexer, pea=None)
    simple_kv_groundtruth_indexer_driver._apply_all(documents)

    assert len(mock_groundtruth_indexer.docs) == 5
    for idx, doc in enumerate(documents):
        print(f' ')
        assert mock_groundtruth_indexer.docs[idx + 1] == doc.SerializeToString()
