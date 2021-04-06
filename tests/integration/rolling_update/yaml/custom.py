from time import sleep

import numpy as np

from jina.executors.indexers.vector import BaseNumpyIndexer


class MockVectorIndexer(BaseNumpyIndexer):
    def build_advanced_index(self, vecs: 'np.ndarray') -> 'np.ndarray':
        sleep(3)  # simulate initialization takes time
        return vecs

    def query(self, keys: np.ndarray, *args, **kwargs):
        pass
