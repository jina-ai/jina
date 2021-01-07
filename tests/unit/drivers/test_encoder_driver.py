from typing import Any

import numpy as np
import pytest

from jina import Document, DocumentSet
from jina.drivers.encode import EncodeDriver
from jina.executors.encoders import BaseEncoder


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


class MockEncoder(BaseEncoder):
    def __init__(self,
                 driver_batch_size: int,
                 total_num_docs: int,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_batch_size = driver_batch_size
        if self.driver_batch_size:
            self.total_num_docs = total_num_docs
            self.total_passes = int(self.total_num_docs / self.driver_batch_size)
            self.id_pass = 0

    @property
    def is_last_batch(self):
        return self.id_pass == self.total_passes

    def encode(self, data: Any, *args, **kwargs) -> Any:
        # encodes 10 * data into the encoder, so return data
        if self.driver_batch_size:
            if not self.is_last_batch:
                assert len(data) == self.driver_batch_size
            else:
                left_to_run_in_request = self.total_num_docs - (self.driver_batch_size*self.total_passes)
                assert len(data) == left_to_run_in_request
            self.id_pass += 1
        return data


class SimpleEncoderDriver(EncodeDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.mark.parametrize('batch_size', [None, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 20, 100, 10000])
def test_encode_driver(batch_size, docs_to_encode, num_docs):
    driver = SimpleEncoderDriver(batch_size=batch_size)
    executor = MockEncoder(driver_batch_size=batch_size, total_num_docs=num_docs)
    driver.attach(executor=executor, runtime=None)
    assert len(docs_to_encode) == num_docs
    for doc in docs_to_encode:
        assert doc.embedding is None
    driver._apply_all(docs_to_encode)
    driver._empty_cache()
    assert len(docs_to_encode) == num_docs
    for doc in docs_to_encode:
        assert doc.embedding == doc.blob
