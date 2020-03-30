from typing import Tuple

import numpy as np

from .numpy import NumpyIndexer


class AnnoyIndexer(NumpyIndexer):

    def __init__(self, metric: str = 'euclidean', n_trees: int = 10, *args, **kwargs):
        """
        Initialize an AnnoyIndexer

        :param num_dim: when set to -1, then num_dim is auto decided on first .add()
        :param data_path: index data file managed by the annoy indexer
        :param metric:
        :param n_trees:
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
            for idx, v in enumerate(vecs):
                _index.add_item(idx, v)
            _index.build(self.n_trees)
            return _index
        else:
            return None

    def query(self, keys: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        if keys.dtype != np.float32:
            raise ValueError('vectors should be ndarray of float32')
        all_ret = []
        all_dist = []
        for k in keys:
            ret, dist = self.query_handler.get_nns_by_vector(k, top_k, include_distances=True)
            all_ret.append(self.int2ext_key[ret])
            all_dist.append(dist)
        return np.array(all_ret), np.array(all_dist)
