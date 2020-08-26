__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import gzip
from os import path
from typing import Optional, List, Union, Tuple

import numpy as np

from . import BaseVectorIndexer
from ...helper import cached_property


class BaseNumpyIndexer(BaseVectorIndexer):
    """:class:`BaseNumpyIndexer` stores and loads vector in a compresses binary file """

    def __init__(self,
                 compress_level: int = 1,
                 ref_indexer: 'BaseNumpyIndexer' = None,
                 *args, **kwargs):
        """
        :param compress_level: The compresslevel argument is an integer from 0 to 9 controlling the
                        level of compression; 1 is fastest and produces the least compression,
                        and 9 is slowest and produces the most compression. 0 is no compression
                        at all. The default is 9.
        :param ref_indexer: Bootstrap the current indexer from a ``ref_indexer``. This enables user to switch
                            the query algorithm at the query time.

        """
        super().__init__(*args, **kwargs)
        self.num_dim = None
        self.dtype = None
        self.compress_level = compress_level
        self.key_bytes = b''
        self.key_dtype = None
        self._ref_index_abspath = None

        if ref_indexer:
            # copy the header info of the binary file
            self.num_dim = ref_indexer.num_dim
            self.dtype = ref_indexer.dtype
            self.compress_level = ref_indexer.compress_level
            self.key_bytes = ref_indexer.key_bytes
            self.key_dtype = ref_indexer.key_dtype
            self._size = ref_indexer._size
            # point to the ref_indexer.index_filename
            # so that later in `post_init()` it will load from the referred index_filename
            self._ref_index_abspath = ref_indexer.index_abspath

    def post_init(self):
        """int2ext_key and ext2int_key should not be serialized, thus they must be put into :func:`post_init`. """
        super().post_init()
        self.int2ext_key = None
        self.ext2int_key = None

    @property
    def index_abspath(self) -> str:
        """Get the file path of the index storage

        Use index_abspath

        """
        return getattr(self, '_ref_index_abspath', None) or self.get_file_from_workspace(self.index_filename)

    def get_add_handler(self):
        """Open a binary gzip file for adding new vectors

        :return: a gzip file stream
        """
        return gzip.open(self.index_abspath, 'ab', compresslevel=self.compress_level)

    def get_create_handler(self) -> 'gzip.GzipFile':
        """Create a new gzip file for adding new vectors

        :return: a gzip file stream
        """
        return gzip.open(self.index_abspath, 'wb', compresslevel=self.compress_level)

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs) -> None:
        self._validate_key_vector_shapes(keys, vectors)
        self.write_handler.write(vectors.tobytes())
        self.key_bytes += keys.tobytes()
        self.key_dtype = keys.dtype.name
        self._size += keys.shape[0]

    def get_query_handler(self) -> Optional['np.ndarray']:
        """Open a gzip file and load it as a numpy ndarray

        :return: a numpy ndarray of vectors
        """
        vecs = self.raw_ndarray
        if vecs is not None:
            return self.build_advanced_index(vecs)
        else:
            return None

    def build_advanced_index(self, vecs: 'np.ndarray'):
        """
        Build advanced index structure based on in-memory numpy ndarray, e.g. graph, tree, etc.

        :param vecs: the raw numpy ndarray
        :return:
        """
        raise NotImplementedError

    def _load_gzip(self, abspath: str) -> Optional['np.ndarray']:
        self.logger.info(f'loading index from {abspath}...')
        if not path.exists(abspath):
            self.logger.warning('numpy data not found: {}'.format(abspath))
            return None
        result = None
        try:
            if self.num_dim and self.dtype:
                with gzip.open(abspath, 'rb') as fp:
                    result = np.frombuffer(fp.read(), dtype=self.dtype).reshape([-1, self.num_dim])
        except EOFError:
            self.logger.error(
                f'{abspath} is broken/incomplete, perhaps forgot to ".close()" in the last usage?')
        return result

    @cached_property
    def raw_ndarray(self) -> Optional['np.ndarray']:
        vecs = self._load_gzip(self.index_abspath)
        if vecs is None:
            return None

        if self.key_bytes and self.key_dtype:
            self.int2ext_key = np.frombuffer(self.key_bytes, dtype=self.key_dtype)

        if self.int2ext_key is not None and vecs is not None and vecs.ndim == 2:
            if self.int2ext_key.shape[0] != vecs.shape[0]:
                self.logger.error(
                    f'the size of the keys and vectors are inconsistent ({self.int2ext_key.shape[0]} != {vecs.shape[0]}), '
                    f'did you write to this index twice? or did you forget to save indexer?')
                return None
            if vecs.shape[0] == 0:
                self.logger.warning(f'an empty index is loaded')

            self.ext2int_key = {k: idx for idx, k in enumerate(self.int2ext_key)}
            return vecs
        else:
            return None

    def query_by_id(self, ids: Union[List[int], 'np.ndarray'], *args, **kwargs) -> 'np.ndarray':
        int_ids = np.array([self.ext2int_key[j] for j in ids])
        return self.raw_ndarray[int_ids]


def _ext_arrs(A, B):
    nA, dim = A.shape
    A_ext = np.ones((nA, dim * 3))
    A_ext[:, dim:2 * dim] = A
    A_ext[:, 2 * dim:] = A ** 2

    nB = B.shape[0]
    B_ext = np.ones((dim * 3, nB))
    B_ext[:dim] = (B ** 2).T
    B_ext[dim:2 * dim] = -2.0 * B.T
    return A_ext, B_ext


def _euclidean(A, B):
    A_ext, B_ext = _ext_arrs(A, B)
    sqdist = A_ext.dot(B_ext).clip(min=0)
    return np.sqrt(sqdist)


def _cosine(A, B):
    A_ext, B_ext = _ext_arrs(A / np.linalg.norm(A, ord=2, axis=1, keepdims=True),
                             B / np.linalg.norm(B, ord=2, axis=1, keepdims=True))
    return A_ext.dot(B_ext).clip(min=0) / 2


class NumpyIndexer(BaseNumpyIndexer):
    """An exhaustive vector indexers implemented with numpy and scipy. """

    def __init__(self, metric: str = 'euclidean',
                 backend: str = 'numpy',
                 *args, **kwargs):
        """
        :param metric: The distance metric to use. `braycurtis`, `canberra`, `chebyshev`, `cityblock`, `correlation`,
                        `cosine`, `dice`, `euclidean`, `hamming`, `jaccard`, `jensenshannon`, `kulsinski`,
                        `mahalanobis`,
                        `matching`, `minkowski`, `rogerstanimoto`, `russellrao`, `seuclidean`, `sokalmichener`,
                        `sokalsneath`, `sqeuclidean`, `wminkowski`, `yule`.
        :param backend: `numpy` or `scipy`, `numpy` only supports `euclidean` and `cosine` distance

        .. note::
            Metrics other than `cosine` and `euclidean` requires ``scipy`` installed.

        """
        super().__init__(*args, **kwargs)
        self.metric = metric
        self.backend = backend

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        """ Find the top-k vectors with smallest ``metric`` and return their ids.

        :return: a tuple of two ndarray.
            The first is ids in shape B x K (`dtype=int`), the second is metric in shape B x K (`dtype=float`)

        .. warning::
            This operation is memory-consuming.

            Distance (the smaller the better) is returned, not the score.

        """
        if self.metric not in {'cosine', 'euclidean'} or self.backend == 'scipy':
            try:
                from scipy.spatial.distance import cdist
                dist = cdist(keys, self.query_handler, metric=self.metric)
            except ModuleNotFoundError:
                self.logger.error(f'your metric {self.metric} requires scipy, but scipy is not found')
        elif self.metric == 'euclidean':
            dist = _euclidean(keys, self.query_handler)
        elif self.metric == 'cosine':
            dist = _cosine(keys, self.query_handler)

        # idx = np.argpartition(dist, kth=top_k, axis=1)[:, :top_k] # To be changed when Doc2DocRanker is available
        idx = dist.argsort(axis=1)[:, :top_k]
        dist = np.take_along_axis(dist, idx, axis=1)
        return self.int2ext_key[idx], dist

    def build_advanced_index(self, vecs: 'np.ndarray'):
        return vecs
