__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

import numpy as np

from .numpy import NumpyIndexer


class NmslibIndexer(NumpyIndexer):
    """nmslib powered vector indexer

    For documentation and explanation of each parameter, please refer to

        - https://nmslib.github.io/nmslib/quickstart.html
        - https://github.com/nmslib/nmslib/blob/master/manual/methods.md

    .. note::
        Nmslib package dependency is only required at the query time.
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
        idx, dist = zip(*ret)
        return self.int2ext_key[np.array(idx)], np.array(dist)
