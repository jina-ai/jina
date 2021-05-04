import io
import os
from functools import lru_cache
from os import path
from typing import Optional, Tuple, Dict, Union

import numpy as np

from . import BaseIndexer
from ..decorators import batching, requests
from ... import DocumentArray
from ...helper import cached_property
from ...importer import ImportExtensions


class VectorIndexer(BaseIndexer):
    batch_size = 512

    def __init__(
            self,
            metric: str = 'cosine',
            backend: str = 'numpy',
            **kwargs,
    ):
        super().__init__(**kwargs)

        self.metric = metric
        self.backend = backend
        self.num_dim = None
        self.dtype = None
        self.key_bytes = b''

    def get_add_handler(self) -> 'io.BufferedWriter':
        """Open a binary gzip file for appending new vectors
        :return: a gzip file stream
        """
        return open(self.index_abspath, 'ab')

    def get_create_handler(self) -> 'io.BufferedWriter':
        """Create a new gzip file for adding new vectors. The old vectors are replaced.
        :return: a gzip file stream
        """
        return open(self.index_abspath, 'wb')

    def _validate_key_vector_shapes(self, keys, vectors):
        if len(vectors.shape) != 2:
            raise ValueError(
                f'vectors shape {vectors.shape} is not valid, expecting "vectors" to have rank of 2'
            )

        if not getattr(self, 'num_dim', None):
            self.num_dim = vectors.shape[1]
            self.dtype = vectors.dtype.name
        elif self.num_dim != vectors.shape[1]:
            raise ValueError(
                f'vectors shape {vectors.shape} does not match with indexers\'s dim: {self.num_dim}'
            )
        elif self.dtype != vectors.dtype.name:
            raise TypeError(
                f'vectors\' dtype {vectors.dtype.name} does not match with indexers\'s dtype: {self.dtype}'
            )

        if keys.shape[0] != vectors.shape[0]:
            raise ValueError(
                f'number of key {keys.shape[0]} not equal to number of vectors {vectors.shape[0]}'
            )

    def add(self, docs: 'DocumentArray', **kwargs) -> None:
        """Add the embeddings and document ids to the index.
        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param vectors: embeddings
        :param args: not used
        :param kwargs: not used
        """
        ids, vectors = docs.extract_fields('id', 'embedding', stack_contents=[False, True])
        keys = np.array(ids, (np.str_, self.key_length))
        if keys.size and vectors.size:
            self._validate_key_vector_shapes(keys, vectors)
            self.write_handler.write(vectors.tobytes())

            self.key_bytes += keys.tobytes()
            self._size += keys.shape[0]

    def get_query_handler(self) -> Optional['np.ndarray']:
        """Open a gzip file and load it as a numpy ndarray
        :return: a numpy ndarray of vectors
        """
        return self._raw_ndarray

    @cached_property
    def _raw_ndarray(self) -> Union['np.ndarray', 'np.memmap', None]:
        if not (path.exists(self.index_abspath) or self.num_dim or self.dtype):
            return

        if self.size is not None and os.stat(self.index_abspath).st_size:
            self.logger.success(f'memmap is enabled for {self.index_abspath}')
            # `==` is required. `is False` does not work in np
            return np.memmap(
                self.index_abspath,
                dtype=self.dtype,
                mode='r',
                shape=(self.size, self.num_dim),
            )

    @cached_property
    def _int2ext_id(self) -> Optional['np.ndarray']:
        """Convert internal ids (0,1,2,3,4,...) to external ids (random strings)
        .. # noqa: DAR201
        """
        if self.key_bytes:
            r = np.frombuffer(self.key_bytes, dtype=(np.str_, self.key_length))
            # `==` is required. `is False` does not work in np
            if r.shape[0] == self.size == self._raw_ndarray.shape[0]:
                return r
            else:
                self.logger.error(
                    f'the size of the keys and vectors are inconsistent '
                    f'({r.shape[0]}, {self._size}, {self._raw_ndarray.shape[0]}), '
                    f'did you write to this index twice? or did you forget to save indexer?'
                )

    @cached_property
    def _ext2int_id(self) -> Optional[Dict]:
        """Convert external ids (random strings) to internal ids (0,1,2,3,4,...)
        .. # noqa: DAR201
        """
        if self._int2ext_id is not None:
            return {k: idx for idx, k in enumerate(self._int2ext_id)}

    @staticmethod
    def _get_sorted_top_k(
            dist: 'np.array', top_k: int
    ) -> Tuple['np.ndarray', 'np.ndarray']:
        """Find top-k smallest distances in ascending order.
        Idea is to use partial sort to retrieve top-k smallest distances unsorted and then sort these
        in ascending order. Equivalent to full sort but faster for n >> k. If k >= n revert to full sort.
        :param dist: the distances
        :param top_k: nr to limit
        :return: tuple of indices, computed distances
        """
        if top_k >= dist.shape[1]:
            idx = dist.argsort(axis=1)[:, :top_k]
            dist = np.take_along_axis(dist, idx, axis=1)
        else:
            idx_ps = dist.argpartition(kth=top_k, axis=1)[:, :top_k]
            dist = np.take_along_axis(dist, idx_ps, axis=1)
            idx_fs = dist.argsort(axis=1)
            idx = np.take_along_axis(idx_ps, idx_fs, axis=1)
            dist = np.take_along_axis(dist, idx_fs, axis=1)

        return idx, dist

    @requests(on='/search')
    def query(
            self, docs: 'DocumentArray', **kwargs
    ) -> Tuple['np.ndarray', 'np.ndarray']:
        """Find the top-k vectors with smallest ``metric`` and return their ids in ascending order.
        :return: a tuple of two ndarray.
            The first is ids in shape B x K (`dtype=int`), the second is metric in shape B x K (`dtype=float`)
        .. warning::
            This operation is memory-consuming.
            Distance (the smaller the better) is returned, not the score.
        :param vectors: the vectors with which to search
        :param args: not used
        :param kwargs: not used
        :param top_k: nr of results to return
        :return: tuple of indices within matrix and distances
        """

        vectors, doc_pts = docs.all_embeddings

        if self.size == 0:
            return np.array([]), np.array([])
        if self.metric not in {'cosine', 'euclidean'} or self.backend == 'scipy':
            dist = self._cdist(vectors, self.query_handler)
        elif self.metric == 'euclidean':
            _query_vectors = _ext_A(vectors)
            dist = self._euclidean(_query_vectors, self.query_handler)
        elif self.metric == 'cosine':
            _query_vectors = _ext_A(_norm(vectors))
            dist = self._cosine(_query_vectors, self.query_handler)
        else:
            raise NotImplementedError

        idx, dist = self._get_sorted_top_k(dist, top_k)
        indices = self._int2ext_id[idx]
        return indices, dist

    @batching(merge_over_axis=1, slice_on=2)
    def _euclidean(self, cached_A, raw_B):
        data = _ext_B(raw_B)
        return _euclidean(cached_A, data)

    @batching(merge_over_axis=1, slice_on=2)
    def _cosine(self, cached_A, raw_B):
        data = _ext_B(_norm(raw_B))
        return _cosine(cached_A, data)

    @batching(merge_over_axis=1, slice_on=2)
    def _cdist(self, *args, **kwargs):
        with ImportExtensions(required=True):
            from scipy.spatial.distance import cdist
        return cdist(*args, **kwargs, metric=self.metric)


@lru_cache(maxsize=3)
def _get_ones(x, y):
    return np.ones((x, y))


def _ext_A(A):
    nA, dim = A.shape
    A_ext = _get_ones(nA, dim * 3)
    A_ext[:, dim: 2 * dim] = A
    A_ext[:, 2 * dim:] = A ** 2
    return A_ext


def _ext_B(B):
    nB, dim = B.shape
    B_ext = _get_ones(dim * 3, nB)
    B_ext[:dim] = (B ** 2).T
    B_ext[dim: 2 * dim] = -2.0 * B.T
    del B
    return B_ext


def _euclidean(A_ext, B_ext):
    sqdist = A_ext.dot(B_ext).clip(min=0)
    return np.sqrt(sqdist)


def _norm(A):
    return A / np.linalg.norm(A, ord=2, axis=1, keepdims=True)


def _cosine(A_norm_ext, B_norm_ext):
    return A_norm_ext.dot(B_norm_ext).clip(min=0) / 2
