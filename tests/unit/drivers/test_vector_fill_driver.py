from typing import Any

import numpy as np

from jina.drivers.search import VectorFillDriver
from jina.executors.indexers import BaseIndexer
from jina.proto import jina_pb2
from jina.proto.ndarray.generic import GenericNdArray


class MockIndexer(BaseIndexer):
    def query_by_id(self, data: Any, *args, **kwargs) -> Any:
        # encodes 10 * data into the encoder, so return data
        return np.random.random([len(data), 5])


class SimpleFillDriver(VectorFillDriver):

    @property
    def exec_fn(self):
        return self._exec_fn


def create_documents_to_encode(num_docs):
    docs = []
    for idx in range(num_docs):
        doc = jina_pb2.Document()
        docs.append(doc)
    return docs


def test_index_driver():
    docs = create_documents_to_encode(10)
    driver = SimpleFillDriver()
    executor = MockIndexer()
    driver.attach(executor=executor, pea=None)
    assert len(docs) == 10
    for doc in docs:
        assert GenericNdArray(doc.embedding).value is None
    driver._apply_all(docs)
    assert len(docs) == 10
    for doc in docs:
        assert GenericNdArray(doc.embedding).value.shape == (5,)
