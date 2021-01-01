from typing import Iterator

import pytest

from jina.drivers.index import KVIndexDriver
from jina.executors.indexers import BaseKVIndexer
from jina.types.document import Document


class MockGroundTruthIndexer(BaseKVIndexer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs = {}

    def add(self, keys: Iterator[int], values: Iterator[bytes], *args, **kwargs):
        for key, value in zip(keys, values):
            self.docs[key] = value

    def update(self, keys: Iterator[int], values: Iterator[bytes], *args, **kwargs):
        for key, value in zip(keys, values):
            self.docs[key] = value

    def delete(self, keys: Iterator[int], *args, **kwargs):
        for key in keys:
            del self.docs[key]


class SimpleKVIndexDriver(KVIndexDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.fixture(scope='function')
def simple_kv_indexer_driver_add():
    return SimpleKVIndexDriver()


@pytest.fixture(scope='function')
def simple_kv_indexer_driver_update():
    return SimpleKVIndexDriver(method='update')


@pytest.fixture(scope='function')
def simple_kv_indexer_driver_delete():
    return SimpleKVIndexDriver(method='delete')


@pytest.fixture(scope='function')
def mock_groundtruth_indexer():
    return MockGroundTruthIndexer()


@pytest.fixture(scope='function')
def documents():
    docs = []
    for idx in range(5):
        with Document(text=f'{idx}') as d:
            d.id = f'{idx:0>16}'
            docs.append(d)
    return docs


@pytest.fixture(scope='function')
def updated_documents():
    docs = []
    for idx in range(3):
        with Document(text='updated_' + f'{idx}') as d:
            d.id = f'{idx:0>16}'
            docs.append(d)
    return docs


@pytest.fixture(scope='function')
def deleted_documents():
    docs = []
    for idx in range(3):
        with Document() as d:
            d.id = f'{idx:0>16}'
            docs.append(d)
    return docs


def test_kv_index_driver_add(mock_groundtruth_indexer, simple_kv_indexer_driver_add, documents):
    simple_kv_indexer_driver_add.attach(executor=mock_groundtruth_indexer, runtime=None)
    simple_kv_indexer_driver_add._apply_all(documents)

    assert len(mock_groundtruth_indexer.docs) == 5
    for idx, doc in enumerate(documents):
        assert mock_groundtruth_indexer.docs[int(doc.id)] == doc.SerializeToString()


def test_kv_index_driver_update(mock_groundtruth_indexer, simple_kv_indexer_driver_add, simple_kv_indexer_driver_update,
                                documents, updated_documents):
    simple_kv_indexer_driver_add.attach(executor=mock_groundtruth_indexer, runtime=None)
    simple_kv_indexer_driver_add._apply_all(documents)

    simple_kv_indexer_driver_update.attach(executor=mock_groundtruth_indexer, runtime=None)
    simple_kv_indexer_driver_update._apply_all(updated_documents)

    assert len(mock_groundtruth_indexer.docs) == 5
    for idx, doc in enumerate(updated_documents[:3] + documents[3:5]):
        assert mock_groundtruth_indexer.docs[int(doc.id)] == doc.SerializeToString()


def test_kv_index_driver_delete(mock_groundtruth_indexer, simple_kv_indexer_driver_add, simple_kv_indexer_driver_delete,
                                documents, deleted_documents):
    simple_kv_indexer_driver_add.attach(executor=mock_groundtruth_indexer, runtime=None)
    simple_kv_indexer_driver_add._apply_all(documents)

    simple_kv_indexer_driver_delete.attach(executor=mock_groundtruth_indexer, runtime=None)
    simple_kv_indexer_driver_delete._apply_all(deleted_documents)

    assert len(mock_groundtruth_indexer.docs) == 2
    for idx, doc in enumerate(documents[3:5]):
        assert mock_groundtruth_indexer.docs[int(doc.id)] == doc.SerializeToString()

    for idx, doc in enumerate(deleted_documents[:3]):
        assert int(doc.id) not in mock_groundtruth_indexer.docs
