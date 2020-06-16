__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

import numpy as np
import gzip

from .numpy import NumpyIndexer


class FaissIndexer(NumpyIndexer):
    """Faiss powered vector indexer

    For more information about the Faiss supported parameters and installation problems, please consult:
        - https://github.com/spotify/annoy
        - https://github.com/facebookresearch/faiss

    .. note::
        Faiss package dependency is only required at the query time.
    """

    def __init__(self, index_key: str, train_filepath: str, *args, **kwargs):
        """
        Initialize an Faiss Indexer

        :param index_key: index type supported by ``faiss.index_factory``
        :param train_filename: the training data
        """
        super().__init__(*args, **kwargs)
        self.index_key = index_key
        self.train_filepath = train_filepath

    def get_query_handler(self):
        """Load all vectors (in numpy ndarray) into Faiss indexers """
        import faiss
        _index_data = super().get_query_handler()
        if _index_data is None:
            self.logger.warning('loading indexing data failed.')
            return None
        if _index_data.ndim != 2:
            self.logger.warning('the index data should be 2D tensor, {} != 2'.format(_index_data.ndim))
            return None
        self._index = faiss.index_factory(self.num_dim, self.index_key)
        if not self.is_trained:
            _train_data = self._load_training_data(self.train_filepath)
            if _train_data is None:
                self.logger.warning('loading training data failed.')
                return None
            self.train(_train_data)
        self._index.add(_index_data.astype('float32'))
        return self._index

    def query(self, keys: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        if keys.dtype != np.float32:
            raise ValueError('vectors should be ndarray of float32')
        dist, ids = self.query_handler.search(keys, top_k)
        return self.int2ext_key[ids], dist

    def train(self, data: 'np.ndarray', *args, **kwargs):
        _num_samples, _num_dim = data.shape
        if not self.num_dim:
            self.num_dim = _num_dim
        if self.num_dim != _num_dim:
            raise ValueError('training data should have the same number of features as the index, {} != {}'.format(
                self.num_dim, _num_dim))
        if _num_samples < 100 * _num_dim:
            self.logger.warning(
                'training sample size (={}) is suggested to be 10 * num_dim (={})'.format(
                    _num_samples, self.num_dim))
        self._index.train(data)
        self.is_trained = True

    def _load_training_data(self, train_filepath):
        return self._load_numpy(train_filepath)
