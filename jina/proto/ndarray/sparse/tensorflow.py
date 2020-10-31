from typing import List, Tuple

from tensorflow import SparseTensor

from . import BaseSparseNdArray

if False:
    import numpy as np


class SparseNdArray(BaseSparseNdArray):
    """Tensorflow powered sparse ndarray, i.e. SparseTensor
    """

    def sparse_constructor(self, indices: 'np.ndarray', values: 'np.ndarray', shape: List[int]) -> 'SparseTensor':
        return SparseTensor(indices, values, shape)

    def sparse_parser(self, value: 'SparseTensor') -> Tuple['np.ndarray', 'np.ndarray', List[int]]:
        return value.indices.numpy(), value.values.numpy(), value.shape.as_list()
