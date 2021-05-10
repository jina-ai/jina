import numpy as np
import pytest
from google.protobuf.struct_pb2 import ListValue

from jina import Document
from jina.drivers.predict import (
    BinaryPredictDriver,
    MultiLabelPredictDriver,
    OneHotPredictDriver,
    Prediction2DocBlobDriver,
)
from jina.executors.classifiers import BaseClassifier
from jina.types.ndarray.generic import NdArray
from jina.types.arrays import DocumentArray
from tests import random_docs


@pytest.fixture(scope='function')
def num_docs():
    return 10


@pytest.fixture(scope='function')
def docs_to_encode(num_docs):
    docs = []
    for idx in range(num_docs):
        doc = Document(content=np.array([idx]))
        docs.append(doc)
    return DocumentArray(docs)


class MockBinaryPredictDriver(BinaryPredictDriver):
    def exec_fn(self, embedding: 'np.ndarray'):
        random_label = np.random.randint(0, 2, [embedding.shape[0]])
        return random_label.astype(np.int64)


class MockOneHotPredictDriver(OneHotPredictDriver):
    def exec_fn(self, embedding: 'np.ndarray'):
        return np.eye(3)[np.random.choice(3, embedding.shape[0])]


class MockMultiLabelPredictDriver(MultiLabelPredictDriver):
    def exec_fn(self, embedding: 'np.ndarray'):
        return np.eye(3)[np.random.choice(3, embedding.shape[0])]


class MockAllLabelPredictDriver(MultiLabelPredictDriver):
    def exec_fn(self, embedding: 'np.ndarray'):
        return np.ones([embedding.shape[0], 3])


class MockPrediction2DocBlobDriver(Prediction2DocBlobDriver):
    def exec_fn(self, embedding: 'np.ndarray'):
        return np.eye(3)[np.random.choice(3, embedding.shape[0])]


class MockClassifierDriver(BinaryPredictDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


class MockClassifier(BaseClassifier):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def predict(self, content: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        # predict 0 or 1 based on divisiblity by 2
        return (content % 2 == 0).astype(int)


def test_binary_predict_driver():
    docs = DocumentArray(random_docs(2))
    driver = MockBinaryPredictDriver()
    driver._apply_all(docs)

    for d in docs:
        assert d.tags['prediction'] in {'yes', 'no'}
        for c in d.chunks:
            assert c.tags['prediction'] in {'yes', 'no'}


def test_one_hot_predict_driver():
    docs = DocumentArray(random_docs(2))
    driver = MockOneHotPredictDriver(labels=['cat', 'dog', 'human'])
    driver._apply_all(docs)

    for d in docs:
        assert d.tags['prediction'] in {'cat', 'dog', 'human'}
        for c in d.chunks:
            assert c.tags['prediction'] in {'cat', 'dog', 'human'}


def test_multi_label_predict_driver():
    docs = DocumentArray(random_docs(2))
    driver = MockMultiLabelPredictDriver(labels=['cat', 'dog', 'human'])
    driver._apply_all(docs)

    for d in docs:
        assert isinstance(d.tags['prediction'], ListValue)
        for t in d.tags['prediction']:
            assert t in {'cat', 'dog', 'human'}

    docs = DocumentArray(random_docs(2))
    driver = MockAllLabelPredictDriver(labels=['cat', 'dog', 'human'])
    driver._apply_all(docs)

    for d in docs:
        assert isinstance(d.tags['prediction'], ListValue)
        assert list(d.tags['prediction']) == ['cat', 'dog', 'human']


def test_as_blob_driver():
    docs = DocumentArray(random_docs(2))
    driver = MockPrediction2DocBlobDriver()
    driver._apply_all(docs)

    for d in docs:
        assert NdArray(d.blob).value.shape == (3,)


def test_predict_driver_without_embeddings(docs_to_encode, num_docs):
    executor = MockClassifier(total_num_docs=num_docs)
    driver = MockClassifierDriver(fields='content')  # use doc.content to predict tags
    driver.attach(executor=executor, runtime=None)
    assert len(docs_to_encode) == num_docs
    for doc in docs_to_encode:
        assert doc.embedding is None
    driver._apply_all(docs_to_encode)
    assert len(docs_to_encode) == num_docs
    for doc in docs_to_encode:
        assert doc.tags['prediction'] in ['yes', 'no']
