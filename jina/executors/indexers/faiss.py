from typing import Tuple

import numpy as np

from .numpy import NumpyIndexer


class FaissIndexer(NumpyIndexer):
    """A Faiss indexers based on :class:`NumpyIndexer`.

    .. note::
        Faiss package dependency is only required at the query time.
    """

    def __init__(self, index_key: str, *args, **kwargs):
        """
        Initialize an Faiss Indexer

        :param index_key: index type supported by ``faiss.index_factory``
        """
        super().__init__(*args, **kwargs)
        self.index_key = index_key

    def get_query_handler(self):
        """Load all vectors (in numpy ndarray) into Faiss indexers """
        import faiss
        data = super().get_query_handler()
        _index = faiss.index_factory(self.num_dim, self.index_key)
        _index.add(data)
        return _index

    def query(self, keys: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        if keys.dtype != np.float32:
            raise ValueError('vectors should be ndarray of float32')

        score, ids = self.query_handler.search(keys, top_k)

        return self.int2ext_key[ids], score
