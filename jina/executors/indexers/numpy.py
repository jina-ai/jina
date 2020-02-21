import gzip
from typing import Tuple, Optional

import numpy as np

from . import BaseIndexer


class NumpyIndexer(BaseIndexer):
    """An exhaustive vector indexers implemented with numpy and scipy. """

    def __init__(self, metric: str = 'euclidean', compress_level: int = 1, *args, **kwargs):
        """
        :param metric: The distance metric to use. `braycurtis`, `canberra`, `chebyshev`, `cityblock`, `correlation`, 
                        `cosine`, `dice`, `euclidean`, `hamming`, `jaccard`, `jensenshannon`, `kulsinski`, 
                        `mahalanobis`, 
                        `matching`, `minkowski`, `rogerstanimoto`, `russellrao`, `seuclidean`, `sokalmichener`, 
                        `sokalsneath`, `sqeuclidean`, `wminkowski`, `yule`.
        :param compress_level: The compresslevel argument is an integer from 0 to 9 controlling the
                        level of compression; 1 is fastest and produces the least compression,
                        and 9 is slowest and produces the most compression. 0 is no compression
                        at all. The default is 9.
        """
        super().__init__(*args, **kwargs)
        self.num_dim = None
        self.dtype = None
        self.metric = metric
        self.compress_level = compress_level
        self.key_bytes = b''
        self.key_dtype = None
        self.int2ext_key = None

    def get_add_handler(self):
        """Open a binary gzip file for adding new vectors

        :return: a gzip file stream
        """
        return gzip.open(self.index_abspath, 'ab', compresslevel=self.compress_level)

    def get_query_handler(self) -> Optional['np.ndarray']:
        """Open a gzip file and load it as a numpy ndarray

        :return: a numpy ndarray of vectors
        """
        if self.num_dim and self.dtype:
            with gzip.open(self.index_abspath, 'rb') as fp:
                vecs = np.frombuffer(fp.read(), dtype=self.dtype).reshape([-1, self.num_dim])

        if self.key_bytes and self.key_dtype:
            self.int2ext_key = np.frombuffer(self.key_bytes, dtype=self.key_dtype)

        if self.int2ext_key is not None and vecs is not None:
            if self.int2ext_key.shape[0] != vecs.shape[0]:
                raise ValueError('the size of the keys is not as same as the vectors (%d != %d)' % (
                    self.int2ext_key.shape[0], vecs.shape[0]))
            return vecs
        else:
            return None

    def get_create_handler(self):
        """Create a new gzip file for adding new vectors

        :return: a gzip file stream
        """
        return gzip.open(self.index_abspath, 'wb', compresslevel=self.compress_level)

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        if len(vectors.shape) != 2:
            raise ValueError('vectors shape %s is not valid, expecting "vectors" to have rank of 2' % vectors.shape)

        if not self.num_dim:
            self.num_dim = vectors.shape[1]
            self.dtype = vectors.dtype.name
        elif self.num_dim != vectors.shape[1]:
            raise ValueError(
                "vectors' shape [%d, %d] does not match with indexers's dim: %d" %
                (vectors.shape[0], vectors.shape[1], self.num_dim))
        elif self.dtype != vectors.dtype.name:
            raise TypeError(
                "vectors' dtype %s does not match with indexers's dtype: %s" %
                (vectors.dtype.name, self.dtype))
        elif keys.shape[0] != vectors.shape[0]:
            raise ValueError('number of key %d not equal to number of vectors %d' % (keys.shape[0], vectors.shape[0]))
        elif self.key_dtype != keys.dtype.name:
            raise TypeError(
                "keys' dtype %s does not match with indexers keys's dtype: %s" %
                (keys.dtype.name, self.key_dtype))

        self.write_handler.write(vectors.tobytes())
        self.key_bytes += keys.tobytes()
        self.key_dtype = keys.dtype.name
        self._size += keys.shape[0]

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        """ Find the top-k vectors with smallest ``metric`` and return their ids.

        :return: a tuple of two ndarray.
            The first is ids in shape B x K (`dtype=int`), the second is metric in shape B x K (`dtype=float`)

        .. warning::
            This operation is memory-consuming.

            Distance (the smaller the better) is returned, not the score.

        """
        from scipy.spatial.distance import cdist
        dist = cdist(keys, self.query_handler, metric=self.metric)

        idx = dist.argsort(axis=1)[:, :top_k]
        dist = np.take_along_axis(dist, idx, axis=1)

        return self.int2ext_key[idx], dist
