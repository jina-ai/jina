__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import gzip
import io
import os
import random
from functools import lru_cache
from os import path
from typing import Optional, Iterable, Tuple, Dict, Union

import numpy as np

from . import BaseVectorIndexer
from ..decorators import batching
from ...helper import cached_property
from ...importer import ImportExtensions


class BaseNumpyIndexer(BaseVectorIndexer):
    """
    :class:`BaseNumpyIndexer` stores and loads vector in a compresses binary file

    .. note::
        :attr:`compress_level` balances between time and space. By default, :classL`NumpyIndexer` has
        :attr:`compress_level` = 0.

        Setting :attr:`compress_level`>0 gives a smaller file size on the disk in the index time. However, in the query
        time it loads all data into memory at once. Not ideal for large scale application.

        Setting :attr:`compress_level`=0 enables :func:`np.memmap`, which loads data in an on-demand way and
        gives smaller memory footprint in the query time. However, it often gives larger file size on the disk.

    :param compress_level: The compresslevel argument is an integer from 0 to 9 controlling the
                    level of compression; 1 is fastest and produces the least compression,
                    and 9 is slowest and produces the most compression. 0 is no compression
                    at all. The default is 9.
    :param ref_indexer: Bootstrap the current indexer from a ``ref_indexer``. This enables user to switch
                        the query algorithm at the query time.
    :param delete_on_dump: whether to delete the rows marked as delete (see ``valid_indices``)
    """

    def __init__(
        self,
        compress_level: int = 1,
        ref_indexer: Optional['BaseNumpyIndexer'] = None,
        delete_on_dump: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.num_dim = None
        self.dtype = None
        self.delete_on_dump = delete_on_dump
        self.compress_level = compress_level
        self.key_bytes = b''
        self.valid_indices = np.array([], dtype=bool)
        self.ref_indexer_workspace_name = None

        if ref_indexer:
            # copy the header info of the binary file
            self.num_dim = ref_indexer.num_dim
            self.dtype = ref_indexer.dtype
            self.compress_level = ref_indexer.compress_level
            self.key_bytes = ref_indexer.key_bytes
            self.key_length = ref_indexer.key_length
            self._size = ref_indexer._size
            # point to the ref_indexer.index_filename
            # so that later in `post_init()` it will load from the referred index_filename
            self.valid_indices = ref_indexer.valid_indices
            self.index_filename = ref_indexer.index_filename
            self.logger.warning(
                f'\n'
                f'num_dim extracted from `ref_indexer` to {ref_indexer.num_dim} \n'
                f'_size extracted from `ref_indexer` to {ref_indexer._size} \n'
                f'dtype extracted from `ref_indexer` to {ref_indexer.dtype} \n'
                f'compress_level overridden from `ref_indexer` to {ref_indexer.compress_level} \n'
                f'index_filename overridden from `ref_indexer` to {ref_indexer.index_filename}'
            )
            self.ref_indexer_workspace_name = ref_indexer.workspace_name
            self.delete_on_dump = getattr(ref_indexer, 'delete_on_dump', delete_on_dump)

    def _delete_invalid_indices(self):
        valid = self.valid_indices[self.valid_indices == True]  # noqa
        if len(valid) != len(self.valid_indices):
            self._clean_memmap()
            self._post_clean_memmap(valid)

    def _post_clean_memmap(self, valid):
        # here we need to make sure the fields
        # that depend on the valid_indices are cleaned up too
        valid_key_bytes = np.frombuffer(
            self.key_bytes, dtype=(np.str_, self.key_length)
        )[self.valid_indices].tobytes()
        self.key_bytes = valid_key_bytes
        self._size = len(valid)
        self.valid_indices = valid
        del self._int2ext_id
        del self._ext2int_id

    def _clean_memmap(self):
        # clean up the underlying matrix of entries marked for deletion
        # first we need to make sure we flush the writing handler
        if self.write_handler and not self.write_handler.closed:
            with self.write_handler as f:
                f.flush()
            self.handler_mutex = False
        # force the raw_ndarray (underlying matrix) to re-read from disk
        # (needed when there were writing ops to be flushed)
        del self._raw_ndarray
        filtered = self._raw_ndarray[self.valid_indices]
        # we need an intermediary file
        tmp_path = self.index_abspath + 'tmp'

        # write the bytes in the respective files
        if self.compress_level > 0:
            with gzip.open(
                tmp_path, 'wb', compresslevel=self.compress_level
            ) as new_gzip_fh:
                new_gzip_fh.write(filtered.tobytes())
        else:
            with open(tmp_path, 'wb') as filtered_data_fh:
                filtered_data_fh.write(filtered.tobytes())

        os.remove(self.index_abspath)
        os.rename(tmp_path, self.index_abspath)
        # force it to re-read again from the new file
        del self._raw_ndarray

    def __getstate__(self):
        # called on pickle save
        if self.delete_on_dump:
            self._delete_invalid_indices()
        d = super().__getstate__()
        return d

    @property
    def workspace_name(self):
        """Get the workspace name.


        .. # noqa: DAR201
        """
        return (
            self.name
            if self.ref_indexer_workspace_name is None
            else self.ref_indexer_workspace_name
        )

    @property
    def index_abspath(self) -> str:
        """Get the file path of the index storage

        Use index_abspath


        .. # noqa: DAR201
        """
        return self.get_file_from_workspace(self.index_filename)

    def get_add_handler(self) -> 'io.BufferedWriter':
        """Open a binary gzip file for appending new vectors

        :return: a gzip file stream
        """
        if self.compress_level > 0:
            return gzip.open(
                self.index_abspath, 'ab', compresslevel=self.compress_level
            )
        else:
            return open(self.index_abspath, 'ab')

    def get_create_handler(self) -> 'io.BufferedWriter':
        """Create a new gzip file for adding new vectors. The old vectors are replaced.

        :return: a gzip file stream
        """
        if self.compress_level > 0:
            return gzip.open(
                self.index_abspath, 'wb', compresslevel=self.compress_level
            )
        else:
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

    def add(self, keys: Iterable[str], vectors: 'np.ndarray', *args, **kwargs) -> None:
        """Add the embeddings and document ids to the index.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param vectors: embeddings
        :param args: not used
        :param kwargs: not used
        """
        np_keys = np.array(keys, (np.str_, self.key_length))
        self._add(np_keys, vectors)

    def _add(self, keys: 'np.ndarray', vectors: 'np.ndarray'):
        if keys.size and vectors.size:
            self._validate_key_vector_shapes(keys, vectors)
            self.write_handler.write(vectors.tobytes())
            self.valid_indices = np.concatenate(
                (self.valid_indices, np.full(len(keys), True))
            )
            self.key_bytes += keys.tobytes()
            self._size += keys.shape[0]

    def update(
        self, keys: Iterable[str], vectors: 'np.ndarray', *args, **kwargs
    ) -> None:
        """Update the embeddings on the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param vectors: embeddings
        :param args: not used
        :param kwargs: not used
        """
        # noinspection PyTypeChecker
        if self.size:
            keys, values = self._filter_nonexistent_keys_values(
                keys, vectors, self._ext2int_id.keys()
            )
            if keys:
                np_keys = np.array(keys, (np.str_, self.key_length))
                self._delete(np_keys)
                self._add(np_keys, np.array(values))
        else:
            self.logger.error(f'{self!r} is empty, update is aborted')

    def _delete(self, keys):
        if keys.size:
            for key in keys:
                # mark as `False` in mask
                self.valid_indices[self._ext2int_id[key]] = False
                self._size -= 1

    def delete(self, keys: Iterable[str], *args, **kwargs) -> None:
        """Delete the embeddings from the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param args: not used
        :param kwargs: not used
        """
        if self.size:
            keys = self._filter_nonexistent_keys(keys, self._ext2int_id.keys())
            if keys:
                np_keys = np.array(keys, (np.str_, self.key_length))
                self._delete(np_keys)
        else:
            self.logger.error(f'{self!r} is empty, deletion is aborted')

    def get_query_handler(self) -> Optional['np.ndarray']:
        """Open a gzip file and load it as a numpy ndarray

        :return: a numpy ndarray of vectors
        """
        if np.all(self.valid_indices):
            vecs = self._raw_ndarray
        else:
            vecs = self._raw_ndarray[self.valid_indices]

        if vecs is not None:
            return self.build_advanced_index(vecs)

    def build_advanced_index(self, vecs: 'np.ndarray'):
        """Not implemented here.


        .. # noqa: DAR201


        .. # noqa: DAR101
        """
        raise NotImplementedError

    def _load_gzip(self, abspath: str, mode='rb') -> Optional['np.ndarray']:
        try:
            self.logger.info(f'loading index from {abspath}...')
            with gzip.open(abspath, mode) as fp:
                return np.frombuffer(fp.read(), dtype=self.dtype).reshape(
                    [-1, self.num_dim]
                )
        except EOFError:
            self.logger.error(
                f'{abspath} is broken/incomplete, perhaps forgot to ".close()" in the last usage?'
            )

    @cached_property
    def _raw_ndarray(self) -> Union['np.ndarray', 'np.memmap', None]:
        if not (path.exists(self.index_abspath) or self.num_dim or self.dtype):
            return

        if self.compress_level > 0:
            return self._load_gzip(self.index_abspath)
        elif self.size is not None and os.stat(self.index_abspath).st_size:
            self.logger.success(f'memmap is enabled for {self.index_abspath}')
            # `==` is required. `is False` does not work in np
            deleted_keys = len(self.valid_indices[self.valid_indices == False])  # noqa
            return np.memmap(
                self.index_abspath,
                dtype=self.dtype,
                mode='r',
                shape=(self.size + deleted_keys, self.num_dim),
            )

    def sample(self) -> Optional[bytes]:
        """Return a random entry from the indexer for sanity check.

        :return: A random entry from the indexer.
        """
        k = random.sample(list(self._ext2int_id.values()), k=1)[0]
        return self._raw_ndarray[k]

    def __iter__(self):
        return self._raw_ndarray.__iter__()

    def query_by_key(
        self, keys: Iterable[str], *args, **kwargs
    ) -> Optional['np.ndarray']:
        """
        Search the index by the external key (passed during `.add(`).

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param args: not used
        :param kwargs: not used
        :return: ndarray of vectors
        """
        keys = self._filter_nonexistent_keys(keys, self._ext2int_id.keys())
        if keys:
            indices = [self._ext2int_id[key] for key in keys]
            return self._raw_ndarray[indices]
        else:
            return None

    @cached_property
    def _int2ext_id(self) -> Optional['np.ndarray']:
        """Convert internal ids (0,1,2,3,4,...) to external ids (random strings)


        .. # noqa: DAR201
        """
        if self.key_bytes:
            r = np.frombuffer(self.key_bytes, dtype=(np.str_, self.key_length))
            # `==` is required. `is False` does not work in np
            deleted_keys = len(self.valid_indices[self.valid_indices == False])  # noqa
            if r.shape[0] == (self.size + deleted_keys) == self._raw_ndarray.shape[0]:
                return r
            else:
                print(
                    f'the size of the keys and vectors are inconsistent '
                    f'({r.shape[0]}, {self._size}, {self._raw_ndarray.shape[0]}), '
                    f'did you write to this index twice? or did you forget to save indexer?'
                )
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


@lru_cache(maxsize=3)
def _get_ones(x, y):
    return np.ones((x, y))


def _ext_A(A):
    nA, dim = A.shape
    A_ext = _get_ones(nA, dim * 3)
    A_ext[:, dim : 2 * dim] = A
    A_ext[:, 2 * dim :] = A ** 2
    return A_ext


def _ext_B(B):
    nB, dim = B.shape
    B_ext = _get_ones(dim * 3, nB)
    B_ext[:dim] = (B ** 2).T
    B_ext[dim : 2 * dim] = -2.0 * B.T
    del B
    return B_ext


def _euclidean(A_ext, B_ext):
    sqdist = A_ext.dot(B_ext).clip(min=0)
    return np.sqrt(sqdist)


def _norm(A):
    return A / np.linalg.norm(A, ord=2, axis=1, keepdims=True)


def _cosine(A_norm_ext, B_norm_ext):
    return A_norm_ext.dot(B_norm_ext).clip(min=0) / 2


class NumpyIndexer(BaseNumpyIndexer):
    """An exhaustive vector indexers implemented with numpy and scipy.

    .. note::
        Metrics other than `cosine` and `euclidean` requires ``scipy`` installed.

    :param metric: The distance metric to use. `braycurtis`, `canberra`, `chebyshev`, `cityblock`, `correlation`,
                    `cosine`, `dice`, `euclidean`, `hamming`, `jaccard`, `jensenshannon`, `kulsinski`,
                    `mahalanobis`,
                    `matching`, `minkowski`, `rogerstanimoto`, `russellrao`, `seuclidean`, `sokalmichener`,
                    `sokalsneath`, `sqeuclidean`, `wminkowski`, `yule`.
    :param backend: `numpy` or `scipy`, `numpy` only supports `euclidean` and `cosine` distance
    :param compress_level: compression level to use
    """

    batch_size = 512

    def __init__(
        self,
        metric: str = 'cosine',
        backend: str = 'numpy',
        compress_level: int = 0,
        *args,
        **kwargs,
    ):
        super().__init__(*args, compress_level=compress_level, **kwargs)
        self.metric = metric
        self.backend = backend

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

    def query(
        self, vectors: 'np.ndarray', top_k: int, *args, **kwargs
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

        idx, dist = self._get_sorted_top_k(dist, top_k)
        indices = self._int2ext_id[self.valid_indices][idx]
        return indices, dist

    def build_advanced_index(self, vecs: 'np.ndarray') -> 'np.ndarray':
        """
        Build advanced index structure based on in-memory numpy ndarray, e.g. graph, tree, etc.

        :param vecs: The raw numpy ndarray.
        :return: Advanced index.
        """
        return vecs

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


class VectorIndexer(NumpyIndexer):
    """Alias to :class:`NumpyIndexer` """
