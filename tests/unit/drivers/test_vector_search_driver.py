from typing import Tuple

import numpy as np
import pytest

from jina import Document, QueryLang
from jina.drivers.search import VectorSearchDriver
from jina.executors.indexers import BaseVectorIndexer


class MockVectorSearchDriver(VectorSearchDriver):

    @property
    def exec_fn(self):
        return self._exec_fn


class MockVectorSearchDriverWithQS(VectorSearchDriver):

    @property
    def queryset(self):
        q = QueryLang()
        q.name = 'MockVectorSearchDriverWithQS'
        q.priority = 1
        q.parameters['top_k'] = 4
        return [q]


@pytest.fixture
def create_document_to_search():
    # 1-D embedding
    # doc: 1 - chunk: 2 - embedding(2.0)
    #        - chunk: 3 - embedding(3.0)
    #        - chunk: 4 - embedding(4.0)
    #        - chunk: 5 - embedding(5.0)
    # ....
    doc = Document()
    for c in range(10):
        chunk = Document()
        chunk.id = str(c) * 16
        chunk.embedding = np.array([c])
        doc.chunks.append(chunk)
    return doc


def test_vectorsearch_driver_mock_queryset():
    # no queryset
    driver = VectorSearchDriver(top_k=3)
    assert driver.top_k == 3

    # with queryset
    driver = MockVectorSearchDriverWithQS(top_k=3)
    assert driver.top_k == 4


def mock_query(vectors: 'np.ndarray', top_k: int) -> Tuple['np.ndarray', 'np.ndarray']:
    idx = np.zeros((vectors.shape[0], top_k))
    dist = np.zeros((vectors.shape[0], top_k))
    for i, row in enumerate(dist):
        for k in range(top_k):
            row[k] = float(k)
    return idx, dist


def mock_query_by_id(ids: 'np.ndarray'):
    return np.random.random([len(ids), 7])


def test_vectorsearch_driver_mock_indexer(monkeypatch, create_document_to_search):
    driver = MockVectorSearchDriver(top_k=2)
    exec = BaseVectorIndexer()
    monkeypatch.setattr(exec, 'query_by_id', None)
    monkeypatch.setattr(driver, '_exec', exec)
    monkeypatch.setattr(driver, 'runtime', None)
    monkeypatch.setattr(driver, '_exec_fn', mock_query)
    doc = create_document_to_search
    driver._apply_all(doc.chunks)

    for chunk in doc.chunks:
        assert len(chunk.matches) == 2
        for match in chunk.matches:
            assert match.granularity == chunk.granularity
            assert match.score.ref_id == str(chunk.id)
            assert match.embedding is None
        assert chunk.matches[0].score.value == 0.
        assert chunk.matches[1].score.value == 1.


def test_vectorsearch_driver_mock_indexer_with_fill(monkeypatch, create_document_to_search):
    driver = MockVectorSearchDriver(top_k=2, fill_embedding=True)
    exec = BaseVectorIndexer()
    monkeypatch.setattr(exec, 'query_by_id', mock_query_by_id)
    monkeypatch.setattr(driver, '_exec', exec)
    monkeypatch.setattr(driver, 'runtime', None)
    monkeypatch.setattr(driver, '_exec_fn', mock_query)
    doc = create_document_to_search
    driver._apply_all(doc.chunks)

    for chunk in doc.chunks:
        assert chunk.matches[0].embedding.shape == (7,)
        assert chunk.matches[-1].embedding.shape == (7,)
        assert chunk.matches[-1].embedding is not None
