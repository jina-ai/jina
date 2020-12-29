import os
from typing import Optional, Sequence, Union, List, Tuple
from os import path

import numpy as np

from .vector import BaseNumpyIndexer
from ...helper import cached_property
from ..decorators import batching


class CRUDBaseNumpyIndexer(BaseNumpyIndexer):
    def __init__(self,
                 ref_indexer: Optional['BaseNumpyIndexer'] = None,
                 *args, **kwargs):
        super().__init__(ref_indexer=ref_indexer, *args, **kwargs)

        self.valid_indices = np.array([], dtype=bool)

        if ref_indexer:
            # copy the header info of the binary file
            if hasattr(ref_indexer, 'valid_indices'):
                self.valid_indices = ref_indexer.valid_indices

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs) -> None:
        super().add(keys, vectors)
        self.valid_indices = np.concatenate((self.valid_indices, np.full(len(keys), True)))

    def get_query_handler(self) -> Optional['np.ndarray']:
        vecs = self.raw_ndarray[self.valid_indices]
        if vecs is not None:
            return self.build_advanced_index(vecs)

    def update(self, keys: Sequence[int], values: Sequence[bytes], *args, **kwargs) -> None:
        self.delete(keys)
        self.add(np.array(keys), np.array(values))

    def delete(self, keys: Sequence[int], *args, **kwargs) -> None:
        self._check_keys(keys)
        for key in keys:
            # mark as `False` in mask
            self.valid_indices[self.ext2int_id[key]] = False
        self._size = self.size - len(list(keys))

    def _check_keys(self, keys: Sequence[int]) -> None:
        missed = []
        for key in keys:
            # if it never existed or if it's been marked as deleted in the current index
            # using `is False` doesn't work
            if key not in self.ext2int_id.keys() or self.valid_indices[self.ext2int_id[key]] == False:  # noqa
                missed.append(key)
        if missed:
            raise KeyError(f'Key(s) {missed} were not found in {self.save_abspath}')

    def query_by_id(self, ids: Union[List[int], 'np.ndarray'], *args, **kwargs) -> 'np.ndarray':
        self._check_keys(ids)
        indices = [self.ext2int_id[key] for key in ids]
        return self.raw_ndarray[indices]

    @cached_property
    def raw_ndarray(self) -> Optional['np.ndarray']:
        if not (path.exists(self.index_abspath) or self.num_dim or self.dtype):
            return

        if self.compress_level > 0:
            return self._load_gzip(self.index_abspath)
        elif self.size is not None and os.stat(self.index_abspath).st_size:
            self.logger.success(f'memmap is enabled for {self.index_abspath}')
            deleted_keys = len(self.valid_indices[self.valid_indices == False])
            # `==` is required. `is False` does not work in np
            return np.memmap(self.index_abspath, dtype=self.dtype, mode='r',
                             shape=(self.size + deleted_keys, self.num_dim))

    @cached_property
    def int2ext_id(self) -> Optional['np.ndarray']:
        if self.key_bytes and self.key_dtype:
            r = np.frombuffer(self.key_bytes, dtype=self.key_dtype)
            # `==` is required. `is False` does not work in np
            deleted_keys = len(self.valid_indices[self.valid_indices == False])  # noqa
            if r.shape[0] == (self.size + deleted_keys) == self.raw_ndarray.shape[0]:
                return r
            else:
                self.logger.error(
                    f'the size of the keys and vectors are inconsistent '
                    f'({r.shape[0]}, {self._size + deleted_keys}, {self.raw_ndarray.shape[0]}), '
                    f'did you write to this index twice? or did you forget to save indexer?')


from .vector import _ext_A, _ext_B, _euclidean, _cosine, _norm


class CRUDNumpyIndexer(CRUDBaseNumpyIndexer):

    batch_size = 512

    def __init__(self, metric: str = 'cosine',
                 backend: str = 'numpy',
                 compress_level: int = 0,
                 *args, **kwargs):
        super().__init__(*args, compress_level=compress_level, **kwargs)
        self.metric = metric
        self.backend = backend

    @staticmethod
    def _get_sorted_top_k(dist: 'np.array', top_k: int) -> Tuple['np.ndarray', 'np.ndarray']:
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

    def query(self, keys: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple[
        Optional['np.ndarray'], Optional['np.ndarray']]:
        if self.size == 0:
            return None, None
        if self.metric not in {'cosine', 'euclidean'} or self.backend == 'scipy':
            dist = self._cdist(keys, self.query_handler)
        elif self.metric == 'euclidean':
            _keys = _ext_A(keys)
            dist = self._euclidean(_keys, self.query_handler)
        elif self.metric == 'cosine':
            _keys = _ext_A(_norm(keys))
            dist = self._cosine(_keys, self.query_handler)
        else:
            raise NotImplementedError(f'{self.metric} is not implemented')

        idx, dist = self._get_sorted_top_k(dist, top_k)
        indices = self.int2ext_id[self.valid_indices][idx]
        return indices, dist

    def build_advanced_index(self, vecs: 'np.ndarray'):
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
        try:
            from scipy.spatial.distance import cdist
            return cdist(*args, **kwargs, metric=self.metric)
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f'your metric {self.metric} requires scipy, but scipy is not found')
