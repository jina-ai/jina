from copy import deepcopy
from typing import Iterator

import numpy as np
import pytest

from jina import DocumentSet
from jina.drivers.index import VectorIndexDriver
from jina.executors.indexers import BaseVectorIndexer
from jina.types.document import Document


class MockGroundTruthVectorIndexer(BaseVectorIndexer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs = {}

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        for key, value in zip(keys, vectors):
            self.docs[key] = value

    def update(self, keys: Iterator[int], values: Iterator[bytes], *args, **kwargs):
        for key, value in zip(keys, values):
            self.docs[key] = value

    def delete(self, keys: Iterator[int], *args, **kwargs):
        for key in keys:
            del self.docs[key]


class SimpleVectorIndexDriver(VectorIndexDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.fixture(scope='function')
def simple_vector_indexer_driver_add():
    return SimpleVectorIndexDriver()


@pytest.fixture(scope='function')
def simple_vector_indexer_driver_update():
    return SimpleVectorIndexDriver(method='update')


@pytest.fixture(scope='function')
def simple_vector_indexer_driver_delete():
    return SimpleVectorIndexDriver(method='delete')


@pytest.fixture(scope='function')
def mock_groundtruth_indexer():
    return MockGroundTruthVectorIndexer()


@pytest.fixture(scope='function')
def documents():
    docs = []
    for idx in range(5):
        with Document(text=f'{idx}') as d:
            d.id = f'{idx:0>16}'
            d.embedding = np.random.random([10])
            docs.append(d)
    return DocumentSet(docs)


@pytest.fixture(scope='function')
def updated_documents():
    docs = []
    for idx in range(3):
        with Document(text='updated_' + f'{idx}') as d:
            d.id = f'{idx:0>16}'
            d.embedding = np.random.random([10])
            docs.append(d)
    return DocumentSet(docs)


@pytest.fixture(scope='function')
def deleted_documents():
    docs = []
    for idx in range(3):
        with Document() as d:
            d.id = f'{idx:0>16}'
            docs.append(d)
    return DocumentSet(docs)


@pytest.fixture(scope='function')
def empty_documents():
    docs = []
    for idx in range(100, 120):
        with Document() as d:
            d.id = f'{idx:0>16}'
            docs.append(d)
    return DocumentSet(docs)


def test_vector_index_driver_add(mock_groundtruth_indexer, simple_vector_indexer_driver_add, documents):
    simple_vector_indexer_driver_add.attach(executor=mock_groundtruth_indexer, runtime=None)
    simple_vector_indexer_driver_add._apply_all(documents)
    assert len(mock_groundtruth_indexer.docs) == 5
    for idx, doc in enumerate(documents):
        np.testing.assert_equal(mock_groundtruth_indexer.docs[int(doc.id)], doc.embedding)


def test_vector_index_driver_add_bad_docs(mocker, mock_groundtruth_indexer, simple_vector_indexer_driver_add, documents,
                                          empty_documents):
    simple_vector_indexer_driver_add.attach(executor=mock_groundtruth_indexer, runtime=None)
    logger_mock = mocker.Mock()
    pea_mock = mocker.Mock()
    pea_mock.logger = logger_mock
    simple_vector_indexer_driver_add.runtime = pea_mock
    # TODO once https://github.com/jina-ai/jina/pull/1555 is merged union can be declared using '+'
    union = deepcopy(documents)
    for d in empty_documents:
        union.add(d)
    simple_vector_indexer_driver_add._apply_all(union)

    # make sure the warning for bad docs is triggered
    assert logger_mock.mock_calls[0][0] == 'warning'
    assert len(mock_groundtruth_indexer.docs) == 5
    for idx, doc in enumerate(documents):
        np.testing.assert_equal(mock_groundtruth_indexer.docs[int(doc.id)], doc.embedding)
    for idx, doc in enumerate(empty_documents):
        assert int(doc.id) not in mock_groundtruth_indexer.docs


def test_vector_index_driver_update(mock_groundtruth_indexer, simple_vector_indexer_driver_add,
                                    simple_vector_indexer_driver_update,
                                    documents, updated_documents):
    simple_vector_indexer_driver_add.attach(executor=mock_groundtruth_indexer, runtime=None)
    simple_vector_indexer_driver_add._apply_all(documents)

    simple_vector_indexer_driver_update.attach(executor=mock_groundtruth_indexer, runtime=None)
    simple_vector_indexer_driver_update._apply_all(updated_documents)

    assert len(mock_groundtruth_indexer.docs) == 5
    for idx, doc in enumerate(updated_documents):
        np.testing.assert_equal(mock_groundtruth_indexer.docs[int(doc.id)], doc.embedding)
    for idx in range(3, 5):
        doc = documents[idx]
        np.testing.assert_equal(mock_groundtruth_indexer.docs[int(doc.id)], doc.embedding)


def test_vector_index_driver_delete(mock_groundtruth_indexer, simple_vector_indexer_driver_add,
                                    simple_vector_indexer_driver_delete,
                                    documents, deleted_documents):
    simple_vector_indexer_driver_add.attach(executor=mock_groundtruth_indexer, runtime=None)
    simple_vector_indexer_driver_add._apply_all(documents)

    simple_vector_indexer_driver_delete.attach(executor=mock_groundtruth_indexer, runtime=None)
    simple_vector_indexer_driver_delete._apply_all(deleted_documents)

    assert len(mock_groundtruth_indexer.docs) == 2
    for idx in range(3, 5):
        doc = documents[idx]
        np.testing.assert_equal(mock_groundtruth_indexer.docs[int(doc.id)], doc.embedding)

    for idx, doc in enumerate(deleted_documents):
        assert int(doc.id) not in mock_groundtruth_indexer.docs
