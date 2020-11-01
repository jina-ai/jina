import numpy as np
from google.protobuf.struct_pb2 import ListValue

from jina.drivers.predict import BinaryPredictDriver, MultiLabelPredictDriver, OneHotPredictDriver, \
    Prediction2DocBlobDriver
from jina.proto.ndarray.generic import GenericNdArray
from tests import random_docs


class MockBinaryPredictDriver(BinaryPredictDriver):
    def exec_fn(self, embed):
        random_label = np.random.randint(0, 1, [embed.shape[0]])
        return random_label.astype(np.int64)


class MockOneHotPredictDriver(OneHotPredictDriver):
    def exec_fn(self, embed):
        return np.eye(3)[np.random.choice(3, embed.shape[0])]


class MockMultiLabelPredictDriver(MultiLabelPredictDriver):
    def exec_fn(self, embed):
        return np.eye(3)[np.random.choice(3, embed.shape[0])]


class MockAllLabelPredictDriver(MultiLabelPredictDriver):
    def exec_fn(self, embed):
        return np.ones([embed.shape[0], 3])


class MockPrediction2DocBlobDriver(Prediction2DocBlobDriver):
    def exec_fn(self, embed):
        return np.eye(3)[np.random.choice(3, embed.shape[0])]


def test_binary_predict_driver():
    docs = list(random_docs(2))
    driver = MockBinaryPredictDriver()
    driver._traverse_apply(docs)

    for d in docs:
        assert d.tags['prediction'] in {'yes', 'no'}
        for c in d.chunks:
            assert c.tags['prediction'] in {'yes', 'no'}


def test_one_hot_predict_driver():
    docs = list(random_docs(2))
    driver = MockOneHotPredictDriver(labels=['cat', 'dog', 'human'])
    driver._traverse_apply(docs)

    for d in docs:
        assert d.tags['prediction'] in {'cat', 'dog', 'human'}
        for c in d.chunks:
            assert c.tags['prediction'] in {'cat', 'dog', 'human'}


def test_multi_label_predict_driver():
    docs = list(random_docs(2))
    driver = MockMultiLabelPredictDriver(labels=['cat', 'dog', 'human'])
    driver._traverse_apply(docs)

    for d in docs:
        assert isinstance(d.tags['prediction'], ListValue)
        for t in d.tags['prediction']:
            assert t in {'cat', 'dog', 'human'}

    docs = list(random_docs(2))
    driver = MockAllLabelPredictDriver(labels=['cat', 'dog', 'human'])
    driver._traverse_apply(docs)

    for d in docs:
        assert isinstance(d.tags['prediction'], ListValue)
        assert list(d.tags['prediction']) == ['cat', 'dog', 'human']


def test_as_blob_driver():
    docs = list(random_docs(2))
    driver = MockPrediction2DocBlobDriver()
    driver._traverse_apply(docs)

    for d in docs:
        assert GenericNdArray(d.blob).value.shape == (3,)
