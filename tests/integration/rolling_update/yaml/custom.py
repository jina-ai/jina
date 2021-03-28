from time import sleep
from typing import Optional

import numpy as np

from jina.executors.indexers.vector import BaseNumpyIndexer


class MockVectorIndexer(BaseNumpyIndexer):

    # def get_query_handler(self) -> Optional['np.ndarray']:
    #     print('### start building index')
    #     sleep(10)  # simulate initialization takes time
    #     print('### finished building index - took 10 seconds')
    #     return None

    def build_advanced_index(self, vecs: 'np.ndarray') -> 'np.ndarray':
        print('### start building index')
        sleep(10)  # simulate initialization takes time
        print('### finished building index - took 10 seconds')
        return vecs

    def query(self, keys: np.ndarray, *args, **kwargs):
        pass
