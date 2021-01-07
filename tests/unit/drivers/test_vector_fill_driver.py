from typing import Any

import numpy as np
import pytest

from jina import Document
from jina.drivers.search import VectorFillDriver
from jina.executors.indexers import BaseIndexer


@pytest.fixture(scope='function')
def num_docs():
    return 10


@pytest.fixture(scope='function')
def docs_to_encode(num_docs):
    docs = []
    for idx in range(num_docs):
        doc = Document(content=np.array([idx]))
        docs.append(doc)
    return docs


class MockIndexer(BaseIndexer):
    def query_by_id(self, data: Any, *args, **kwargs) -> Any:
        # encodes 10 * data into the encoder, so return data
        return np.random.random([len(data), 5])


class SimpleFillDriver(VectorFillDriver):

    @property
    def exec_fn(self):
        return self._exec_fn


def test_index_driver(docs_to_encode, num_docs):
    driver = SimpleFillDriver()
    executor = MockIndexer()
    driver.attach(executor=executor, runtime=None)
    assert len(docs_to_encode) == num_docs
    for doc in docs_to_encode:
        assert doc.embedding is None
    driver._apply_all(docs_to_encode)
    assert len(docs_to_encode) == num_docs
    for doc in docs_to_encode:
        assert doc.embedding.shape == (5,)
