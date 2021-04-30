from typing import Any

import pytest
import numpy as np
from scipy import sparse

from jina import Document, DocumentArray
from jina.drivers.encode import EncodeDriver, ScipySparseEncodeDriver
from jina.executors.encoders import BaseEncoder
from jina.executors.decorators import batching


@pytest.fixture(scope='function')
def num_docs():
    return 10


@pytest.fixture(scope='function')
def docs_to_encode(num_docs):
    docs = []
    for idx in range(1, num_docs + 1):
        doc = Document(content=np.array([idx]))
        docs.append(doc)
    return DocumentArray(docs)


def get_encoder(batch_size):
    class MockEncoder(BaseEncoder):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        @batching(batch_size=batch_size)
        def encode(self, content: 'np.ndarray', *args, **kwargs) -> Any:
            if batch_size is not None and batch_size > 0:
                assert len(content) <= batch_size
            if batch_size == 5:
                assert len(content) == 5
            return content

    return MockEncoder()


class SimpleEncoderDriver(EncodeDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.mark.parametrize(
    'batch_size', [None, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 20, 100, 10000]
)
def test_encode_driver(batch_size, docs_to_encode, num_docs):
    driver = SimpleEncoderDriver()
    executor = get_encoder(batch_size)
    driver.attach(executor=executor, runtime=None)
    assert len(docs_to_encode) == num_docs
    for doc in docs_to_encode:
        assert doc.embedding is None
    driver._apply_all(docs_to_encode)
    assert len(docs_to_encode) == num_docs
    for doc in docs_to_encode:
        assert doc.embedding == doc.blob


def get_sparse_encoder(sparse_type):
    class MockEncoder(BaseEncoder):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def encode(self, content: 'np.ndarray', *args, **kwargs) -> Any:
            # return a sparse vector of the same number of rows as `data` of different types
            embed = sparse_type(content)
            return embed

    return MockEncoder()


class SimpleScipySparseEncoderDriver(ScipySparseEncodeDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.fixture(
    params=[sparse.csr_matrix, sparse.coo_matrix, sparse.bsr_matrix, sparse.csc_matrix]
)
def sparse_type(request):
    return request.param


def test_sparse_encode_driver(sparse_type, docs_to_encode, num_docs):
    driver = SimpleScipySparseEncoderDriver()
    encoder = get_sparse_encoder(sparse_type)
    driver.attach(executor=encoder, runtime=None)
    assert len(docs_to_encode) == num_docs
    for doc in docs_to_encode:
        assert doc.embedding is None
    driver._apply_all(docs_to_encode)
    assert len(docs_to_encode) == num_docs
    for doc in docs_to_encode:
        assert isinstance(doc.embedding, sparse.coo_matrix)
        assert doc.embedding == doc.blob
