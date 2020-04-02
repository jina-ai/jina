from typing import Tuple

import numpy as np

from .numpy import NumpyIndexer


class NmslibIndexer(NumpyIndexer):
    """Indexer powered by nmslib

    For documentation and explaination of each parameter, please refer to

        - https://nmslib.github.io/nmslib/quickstart.html
        - https://github.com/nmslib/nmslib/blob/master/manual/methods.md
    """

    def __init__(self, space: str = 'cosinesimil', method: str = 'hnsw', print_progress: bool = False,
                 num_threads: int = 1,
                 *args, **kwargs):
        """
        Initialize an NmslibIndexer

        :param space: The metric space to create for this index
        :param method: The index method to use
        :param num_threads: The number of threads to use
        :param print_progress: Whether or not to display progress bar when creating index
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.method = method
        self.space = space
        self.print_progress = print_progress
        self.num_threads = num_threads

    def get_query_handler(self):
        vecs = super().get_query_handler()
        if vecs is not None:
            import nmslib
            _index = nmslib.init(method=self.method, space=self.space)
            _index.addDataPointBatch(vecs.astype(np.float32))
            _index.createIndex({'post': 2}, print_progress=self.print_progress)
            return _index
        else:
            return None

    def query(self, keys: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        if keys.dtype != np.float32:
            raise ValueError('vectors should be ndarray of float32')
        ret = self.query_handler.knnQueryBatch(keys, k=top_k, num_threads=self.num_threads)
        idx = np.stack([self.int2ext_key[v[0]] for v in ret])
        dist = np.stack([v[1] for v in ret])
        return idx, dist
