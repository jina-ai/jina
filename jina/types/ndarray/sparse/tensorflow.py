from typing import List

from tensorflow import SparseTensor
from . import BaseSparseNdArray

if False:
    import numpy as np

__all__ = ['SparseNdArray']


class SparseNdArray(BaseSparseNdArray):
    """
    Tensorflow powered sparse ndarray, i.e. SparseTensor.

    .. seealso::
        https://www.tensorflow.org/api_docs/python/tf/sparse/SparseTensor
    """

    def sparse_constructor(
        self, indices: 'np.ndarray', values: 'np.ndarray', shape: List[int]
    ) -> 'SparseTensor':
        """
        Sparse NdArray constructor for Tensorflow.

        :param indices: the indices of the sparse array
        :param values: the values of the sparse array
        :param shape: the shape of the sparse array
        :return: SparseTensor
        """
        return SparseTensor(indices, values, shape)

    def sparse_parser(self, value: 'SparseTensor'):
        """
        Parse a SparseTensor to indices, values and shape.

        :param value: the SparseTensor.
        :return: a Dict with three entries {'indices': ..., 'values':..., 'shape':...}
        """
        return {
            'indices': value.indices.numpy(),
            'values': value.values.numpy(),
            'shape': value.shape.as_list(),
        }
