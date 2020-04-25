__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

import numpy as np

from .numpy import NumpyIndexer


class AnnoyIndexer(NumpyIndexer):
    """Annoy powered vector indexer

    For more information about the Annoy supported parameters, please consult:
        - https://github.com/spotify/annoy

    .. note::
        Annoy package dependency is only required at the query time.
    """

    def __init__(self, metric: str = 'euclidean', n_trees: int = 10, *args, **kwargs):
        """
        Initialize an AnnoyIndexer

        :param metric: Metric can be "angular", "euclidean", "manhattan", "hamming", or "dot"
        :param n_trees: builds a forest of n_trees trees. More trees gives higher precision when querying.
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.metric = metric
        self.n_trees = n_trees

    def get_query_handler(self):
        vecs = super().get_query_handler()
        if vecs is not None:
            from annoy import AnnoyIndex
            _index = AnnoyIndex(self.num_dim, self.metric)
            vecs = vecs.astype(np.float32)
            for idx, v in enumerate(vecs):
                _index.add_item(idx, v)
            _index.build(self.n_trees)
            return _index
        else:
            return None

    def query(self, keys: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        if keys.dtype != np.float32:
            raise ValueError('vectors should be ndarray of float32')
        all_idx = []
        all_dist = []
        for k in keys:
            ret, dist = self.query_handler.get_nns_by_vector(k, top_k, include_distances=True)
            all_idx.append(self.int2ext_key[ret])
            all_dist.append(dist)
        return np.array(all_idx), np.array(all_dist)
