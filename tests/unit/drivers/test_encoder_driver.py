from typing import Any

import pytest
import numpy as np

from jina import Document, DocumentSet
from jina.drivers.encode import EncodeDriver
from jina.executors.encoders import BaseEncoder


class MockEncoder(BaseEncoder):
    def __init__(self, driver_batch_size, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_batch_size = driver_batch_size

    def encode(self, data: Any, *args, **kwargs) -> Any:
        # encodes 10 * data into the encoder, so return data
        if self.driver_batch_size:
            assert len(data) == self.driver_batch_size
        return data


class SimpleEncoderDriver(EncodeDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


def create_documents_to_encode(num_docs):
    docs = []
    for idx in range(num_docs):
        doc = Document(content=np.array([idx]))

        docs.append(doc)
    return DocumentSet(docs)


@pytest.mark.parametrize('batch_size', [None, 2, 5, 10, 10000])
def test_encode_driver(batch_size):
    docs = create_documents_to_encode(10)
    driver = SimpleEncoderDriver(batch_size=batch_size)
    executor = MockEncoder(driver_batch_size=batch_size)
    driver.attach(executor=executor, pea=None)
    assert len(docs) == 10
    for doc in docs:
        assert doc.embedding is None
    driver._apply_all(docs)
    assert len(docs) == 10
    for doc in docs:
        assert doc.embedding == doc.blob
