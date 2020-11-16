from typing import List

import numpy as np

from . import BaseSparseNdArray

__all__ = ['SparseNdArray']


class SparseNdArray(BaseSparseNdArray):
    """Numpy powered sparse ndarray, it uses nonzero.

    .. note::
        This always take a dense :class:`np.ndarray` and return a :class:`np.ndarray`.
        It only store nonzero data in sparse format, it does not keep a sparse representation in memory.
    """

    def sparse_constructor(self, indices: 'np.ndarray', values: 'np.ndarray', shape: List[int]) -> 'np.ndarray':
        val = np.zeros(shape)
        val[tuple(indices.T)] = values
        return val

    def sparse_parser(self, value: 'np.ndarray'):
        nv = np.nonzero(value)
        val = value[nv]
        indices = np.transpose(nv)
        return {'indices': indices,
                'values': val,
                'shape': list(value.shape)}
