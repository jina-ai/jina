from typing import Any

import numpy as np
import pytest

from jina import Document, DocumentSet
from jina.drivers.encode import EncodeDriver
from jina.executors.encoders import BaseEncoder
from jina.executors.decorators import batching


@pytest.fixture(scope='function')
def num_docs():
    return 10


@pytest.fixture(scope='function')
def docs_to_encode(num_docs):
    docs = []
    for idx in range(num_docs):
        doc = Document(content=np.array([idx]))
        docs.append(doc)
    return DocumentSet(docs)


def get_encoder(batch_size):
    class MockEncoder(BaseEncoder):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        @batching(batch_size=batch_size)
        def encode(self, data: Any, *args, **kwargs) -> Any:
            if batch_size is not None and batch_size > 0:
                assert len(data) <= batch_size
            if batch_size == 5:
                assert len(data) == 5
            return data

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
