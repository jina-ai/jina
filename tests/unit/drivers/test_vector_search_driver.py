from typing import Tuple

import numpy as np
import scipy
import torch
import tensorflow as tf
import pytest

from jina import Document, QueryLang
from jina.drivers.search import VectorSearchDriver
from jina.executors.indexers import BaseVectorIndexer


def embedding_cls_type_supported():
    return ['dense', 'scipy_csr', 'scipy_coo', 'torch', 'tf']


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


@pytest.fixture(scope='function')
def documents_factory():
    def documents(embedding_cls_type):
        doc = Document()
        for c in range(10):
            chunk = Document()
            chunk.id = str(c) * 16
            dense_embedding = np.random.random([10])
            if embedding_cls_type == 'dense':
                chunk.embedding = dense_embedding
            elif embedding_cls_type == 'scipy_csr':
                chunk.embedding = scipy.sparse.csr_matrix(dense_embedding)
            elif embedding_cls_type == 'scipy_coo':
                chunk.embedding = scipy.sparse.coo_matrix(dense_embedding)
            elif embedding_cls_type == 'torch':
                sparse_embedding = scipy.sparse.coo_matrix(dense_embedding)
                values = sparse_embedding.data
                indices = np.vstack((sparse_embedding.row, sparse_embedding.col))
                chunk.embedding = torch.sparse_coo_tensor(
                    indices,
                    values,
                    sparse_embedding.shape,
                )
            elif embedding_cls_type == 'tf':
                sparse_embedding = scipy.sparse.coo_matrix(dense_embedding)
                values = sparse_embedding.data
                indices = [
                    (x, y) for x, y in zip(sparse_embedding.row, sparse_embedding.col)
                ]
                chunk.embedding = tf.SparseTensor(
                    indices=indices,
                    values=values,
                    dense_shape=[1, 10],
                )
            doc.chunks.append(chunk)
        return doc

    return documents


def test_vectorsearch_driver_mock_queryset():
    # no queryset
    driver = VectorSearchDriver(top_k=3)
    assert driver.top_k == 3

    # with queryset
    driver = MockVectorSearchDriverWithQS(top_k=3)
    assert driver.top_k == 4


def mock_query(vectors, top_k: int) -> Tuple['np.ndarray', 'np.ndarray']:
    idx = np.zeros((vectors.shape[0], top_k), dtype=(np.str_, 16))
    dist = np.zeros((vectors.shape[0], top_k))
    for i, row in enumerate(dist):
        for k in range(top_k):
            row[k] = float(k)
    return idx, dist


def mock_query_by_key(keys: 'np.ndarray'):
    return np.random.random([len(keys), 7])


@pytest.mark.parametrize('embedding_cls_type', embedding_cls_type_supported())
def test_vectorsearch_driver_mock_indexer(
    monkeypatch, documents_factory, embedding_cls_type
):
    driver = MockVectorSearchDriver(top_k=2)
    index = BaseVectorIndexer()
    monkeypatch.setattr(index, 'query_by_key', None)
    monkeypatch.setattr(driver, '_exec', index)
    monkeypatch.setattr(driver, 'runtime', None)
    monkeypatch.setattr(driver, '_exec_fn', mock_query)
    doc = documents_factory(embedding_cls_type)
    driver._apply_all(doc.chunks)

    for chunk in doc.chunks:
        assert len(chunk.matches) == 2
        for match in chunk.matches:
            assert match.granularity == chunk.granularity
            assert match.score.ref_id == str(chunk.id)
            assert match.embedding is None
        assert chunk.matches[0].score.value == 0.0
        assert chunk.matches[1].score.value == 1.0


@pytest.mark.parametrize('embedding_cls_type', embedding_cls_type_supported())
def test_vectorsearch_driver_mock_indexer_with_fill(
    monkeypatch, documents_factory, embedding_cls_type
):
    driver = MockVectorSearchDriver(top_k=2, fill_embedding=True)
    index = BaseVectorIndexer()
    monkeypatch.setattr(index, 'query_by_key', mock_query_by_key)
    monkeypatch.setattr(driver, '_exec', index)
    monkeypatch.setattr(driver, 'runtime', None)
    monkeypatch.setattr(driver, '_exec_fn', mock_query)
    doc = documents_factory(embedding_cls_type)
    driver._apply_all(doc.chunks)

    for chunk in doc.chunks:
        assert chunk.matches[0].embedding.shape == (7,)
        assert chunk.matches[-1].embedding.shape == (7,)
        assert chunk.matches[-1].embedding is not None
