import numpy as np

from jina.executors.indexers import BaseIndexer
from tests import JinaTestCase


class DummyIndexerTrain(BaseIndexer):

    def train(self, data: 'np.ndarray', *args, **kwargs):
        pass


class MyTestCase(JinaTestCase):

    def test_calling_train_sets_is_trained(self):
        data = np.random.rand(1, 2)
        i = DummyIndexerTrain(index_filename='test2.bin')

        # Call train method on indexer
        i.train(data)
        # After train was called, is_trained must be true
        self.assertTrue(i.is_trained)
