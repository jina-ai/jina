__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

import numpy as np

from .numpy import NumpyIndexer


class FaissIndexer(NumpyIndexer):
    """Faiss powered vector indexer

    For more information about the Faiss supported parameters and installation problems, please consult:
        - https://github.com/spotify/annoy
        - https://github.com/facebookresearch/faiss

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

        dist, ids = self.query_handler.search(keys, top_k)

        # ids is already a numpy array
        return self.int2ext_key[ids], dist
