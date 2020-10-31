from typing import Any

import numpy as np

from jina.drivers.encode import EncodeDriver
from jina.executors.encoders import BaseEncoder
from jina.proto import jina_pb2
from jina.proto.ndarray.generic import GenericNdArray


class MockEncoder(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def encode(self, data: Any, *args, **kwargs) -> Any:
        # encodes 10 * data into the encoder, so return data
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
        doc = jina_pb2.Document()
        GenericNdArray(doc.blob).value = np.array([idx])
        docs.append(doc)
    return docs


def test_encode_driver():
    docs = create_documents_to_encode(10)
    driver = SimpleEncoderDriver()
    executor = MockEncoder()
    driver.attach(executor=executor, pea=None)
    assert len(docs) == 10
    for doc in docs:
        assert GenericNdArray(doc.embedding).value is None
    driver._apply_all(docs)
    assert len(docs) == 10
    for doc in docs:
        assert doc.embedding == doc.blob
