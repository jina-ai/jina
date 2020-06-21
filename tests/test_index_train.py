import numpy as np

from jina.executors.indexers.vector.numpy import NumpyIndexer
from tests import JinaTestCase


class DummyIndexer(NumpyIndexer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, index_filename="test.bin")

    def train(self, data: 'np.ndarray', *args, **kwargs):
        pass


class MyTestCase(JinaTestCase):

    def test_calling_train_sets_is_trained(self):
        data = np.random.rand(1, 2)
        i = DummyIndexer()
        # Call train method on indexer
        i.train(data)
        # After train was called, is_trained must be true
        self.assertTrue(i.is_trained)
