from copy import deepcopy

import numpy as np
import scipy
import torch
import tensorflow as tf
import pytest

from jina import DocumentArray
from jina.drivers.delete import DeleteDriver
from jina.drivers.index import VectorIndexDriver
from jina.executors.indexers import BaseVectorIndexer
from jina.types.document import Document


def embedding_cls_type_supported():
    return ['dense', 'scipy_csr', 'scipy_coo', 'torch', 'tf']


class MockGroundTruthVectorIndexer(BaseVectorIndexer):
    def __init__(self, embedding_cls_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs = {}
        self.embedding_cls_type = embedding_cls_type

    def add(self, keys, vectors, *args, **kwargs):
        if self.embedding_cls_type in ['dense', 'torch', 'tf']:
            for key, value in zip(keys, vectors):
                self.docs[key] = value
        elif self.embedding_cls_type.startswith('scipy'):
            for i, key in enumerate(keys):
                self.docs[key] = vectors.getrow(i)

    def update(self, keys, vectors, *args, **kwargs) -> None:
        if self.embedding_cls_type in ['dense', 'torch', 'tf']:
            for key, value in zip(keys, vectors):
                self.docs[key] = value
        elif self.embedding_cls_type.startswith('scipy'):
            for i, key in enumerate(keys):
                self.docs[key] = vectors.getrow(i)

    def delete(self, keys, *args, **kwargs) -> None:
        for key in keys:
            del self.docs[key]


class SimpleVectorIndexDriver(VectorIndexDriver):
    @property
    def exec_fn(self):
        return self._exec_fn


class SimpleDeleteDriver(DeleteDriver):
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
    return SimpleDeleteDriver()


@pytest.fixture(scope='function')
def mock_groundtruth_indexer_factory():
    def indexer(embedding_cls_type):
        return MockGroundTruthVectorIndexer(embedding_cls_type)

    return indexer


@pytest.fixture(scope='function')
def documents_factory():
    def documents(embedding_cls_type, text_prefix='', num_docs=5):
        docs = []
        for idx in range(num_docs):
            with Document(text=f'{text_prefix}{idx}') as d:
                d.id = f'{idx:0>16}'
                dense_embedding = np.random.random([10])
                if embedding_cls_type == 'dense':
                    d.embedding = dense_embedding
                elif embedding_cls_type == 'scipy_csr':
                    d.embedding = scipy.sparse.csr_matrix(dense_embedding)
                elif embedding_cls_type == 'scipy_coo':
                    d.embedding = scipy.sparse.coo_matrix(dense_embedding)
                elif embedding_cls_type == 'torch':
                    sparse_embedding = scipy.sparse.coo_matrix(dense_embedding)
                    values = sparse_embedding.data
                    indices = np.vstack((sparse_embedding.row, sparse_embedding.col))
                    d.embedding = torch.sparse_coo_tensor(
                        indices,
                        values,
                        sparse_embedding.shape,
                    )
                elif embedding_cls_type == 'tf':
                    sparse_embedding = scipy.sparse.coo_matrix(dense_embedding)
                    values = sparse_embedding.data
                    indices = [
                        (x, y)
                        for x, y in zip(sparse_embedding.row, sparse_embedding.col)
                    ]
                    d.embedding = tf.SparseTensor(
                        indices=indices,
                        values=values,
                        dense_shape=[1, 10],
                    )
            docs.append(d)
        return DocumentArray(docs)

    return documents


@pytest.fixture(scope='function')
def deleted_documents():
    docs = []
    for idx in range(3):
        with Document() as d:
            d.id = f'{idx:0>16}'
            docs.append(d)
    return DocumentArray(docs)


@pytest.fixture(scope='function')
def empty_documents():
    docs = []
    for idx in range(100, 120):
        with Document() as d:
            d.id = f'{idx:0>16}'
            docs.append(d)
    return DocumentArray(docs)


def assert_embedding(embedding_cls_type, obtained, expected):
    if embedding_cls_type == 'dense':
        np.testing.assert_equal(obtained, expected.embedding)
    elif embedding_cls_type.startswith('scipy'):
        np.testing.assert_equal(obtained.todense(), expected.embedding.todense())
    elif embedding_cls_type == 'torch':
        from jina.types.ndarray.sparse.pytorch import SparseNdArray

        np.testing.assert_array_equal(
            expected.get_sparse_embedding(sparse_ndarray_cls_type=SparseNdArray)[0]
            .to_dense()
            .numpy(),
            obtained.to_dense().numpy(),
        )
    elif embedding_cls_type == 'tf':
        from jina.types.ndarray.sparse.tensorflow import SparseNdArray

        np.testing.assert_array_equal(
            tf.sparse.to_dense(
                expected.get_sparse_embedding(sparse_ndarray_cls_type=SparseNdArray)
            ).numpy(),
            tf.sparse.to_dense(obtained).numpy(),
        )


@pytest.mark.parametrize('embedding_cls_type', embedding_cls_type_supported())
def test_vector_index_driver_add(
    simple_vector_indexer_driver_add,
    mock_groundtruth_indexer_factory,
    documents_factory,
    embedding_cls_type,
):
    indexer = mock_groundtruth_indexer_factory(embedding_cls_type)
    documents = documents_factory(embedding_cls_type)
    simple_vector_indexer_driver_add.attach(executor=indexer, runtime=None)
    simple_vector_indexer_driver_add._apply_all(documents)
    assert len(indexer.docs) == 5
    for idx, doc in enumerate(documents):
        assert_embedding(embedding_cls_type, indexer.docs[doc.id], doc)


@pytest.mark.parametrize('embedding_cls_type', embedding_cls_type_supported())
def test_vector_index_driver_add_bad_docs(
    mocker,
    mock_groundtruth_indexer_factory,
    simple_vector_indexer_driver_add,
    documents_factory,
    empty_documents,
    embedding_cls_type,
):
    indexer = mock_groundtruth_indexer_factory(embedding_cls_type)
    documents = documents_factory(embedding_cls_type)
    simple_vector_indexer_driver_add.attach(executor=indexer, runtime=None)
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
    assert len(indexer.docs) == 5
    for idx, doc in enumerate(documents):
        assert_embedding(embedding_cls_type, indexer.docs[doc.id], doc)
    for idx, doc in enumerate(empty_documents):
        assert doc.id not in indexer.docs


@pytest.mark.parametrize('embedding_cls_type', embedding_cls_type_supported())
def test_vector_index_driver_update(
    mock_groundtruth_indexer_factory,
    simple_vector_indexer_driver_add,
    simple_vector_indexer_driver_update,
    documents_factory,
    embedding_cls_type,
):
    indexer = mock_groundtruth_indexer_factory(embedding_cls_type)
    documents = documents_factory(embedding_cls_type)
    updated_documents = documents_factory(embedding_cls_type, 'update', 3)
    simple_vector_indexer_driver_add.attach(executor=indexer, runtime=None)
    simple_vector_indexer_driver_add._apply_all(documents)

    simple_vector_indexer_driver_update.attach(executor=indexer, runtime=None)
    simple_vector_indexer_driver_update._apply_all(updated_documents)

    assert len(indexer.docs) == 5
    for idx, doc in enumerate(updated_documents):
        assert_embedding(embedding_cls_type, indexer.docs[doc.id], doc)
    for idx in range(3, 5):
        doc = documents[idx]
        assert_embedding(embedding_cls_type, indexer.docs[doc.id], doc)


@pytest.mark.parametrize('embedding_cls_type', embedding_cls_type_supported())
def test_vector_index_driver_delete(
    mock_groundtruth_indexer_factory,
    simple_vector_indexer_driver_add,
    simple_vector_indexer_driver_delete,
    documents_factory,
    deleted_documents,
    mocker,
    embedding_cls_type,
):
    indexer = mock_groundtruth_indexer_factory(embedding_cls_type)
    documents = documents_factory(embedding_cls_type)
    simple_vector_indexer_driver_add.attach(executor=indexer, runtime=None)
    simple_vector_indexer_driver_add._apply_all(documents)

    simple_vector_indexer_driver_delete.attach(executor=indexer, runtime=None)
    mock_load = mocker.patch.object(
        simple_vector_indexer_driver_delete, 'runtime', autospec=True
    )
    mock_load.request.ids = [d.id for d in deleted_documents]
    simple_vector_indexer_driver_delete()

    assert len(indexer.docs) == 2
    for idx in range(3, 5):
        doc = documents[idx]
        assert_embedding(embedding_cls_type, indexer.docs[doc.id], doc)

    for idx, doc in enumerate(deleted_documents):
        assert doc.id not in indexer.docs
