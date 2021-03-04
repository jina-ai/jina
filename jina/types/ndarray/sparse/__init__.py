from typing import List, TypeVar, Union, Dict

from .. import BaseNdArray
from ..dense.numpy import DenseNdArray
from ....proto import jina_pb2

AnySparseNdArray = TypeVar('AnySparseNdArray')

if False:
    import numpy as np

__all__ = ['BaseSparseNdArray']


class BaseSparseNdArray(BaseNdArray):
    """
    The base class for :class:`SparseNdArray`.

    Do not use this class directly. Subclass should be used.

    """

    def __init__(self, *args, **kwargs):
        """Set constructor method."""
        super().__init__(*args, **kwargs)
        self.is_sparse = True

    def null_proto(self):
        """Get the new protobuf representation."""
        return jina_pb2.SparseNdArrayProto()

    def sparse_constructor(
        self, indices: 'np.ndarray', values: 'np.ndarray', shape: List[int]
    ) -> AnySparseNdArray:
        """
        Sparse NdArray constructor, must be implemented by subclass.

        :param indices: the indices of the sparse array
        :param values: the values of the sparse array
        :param shape: the shape of the sparse array
        :return: Sparse NdArray
        """
        raise NotImplementedError

    def sparse_parser(
        self, value: AnySparseNdArray
    ) -> Dict[str, Union['np.ndarray', List[int]]]:
        """
        Parse a Sparse NdArray to indices, values and shape, must be implemented by subclass.

        :param value: the sparse ndarray
        :return: a Dict with three entries {'indices': ..., 'values':..., 'shape':...}
        """
        raise NotImplementedError

    @property
    def value(self) -> AnySparseNdArray:
        """Get the value of protobuf message in :class:`SparseNdArray`."""
        idx = DenseNdArray(self._pb_body.indices).value
        val = DenseNdArray(self._pb_body.values).value
        shape = self._pb_body.dense_shape
        if idx is not None and val is not None and shape:
            return self.sparse_constructor(idx, val, shape)

    @value.setter
    def value(self, value: AnySparseNdArray):
        """Set the value of protobuf message with :param:`value` in :class:`SparseNdArray`."""
        r = self.sparse_parser(value)
        DenseNdArray(self._pb_body.indices).value = r['indices']
        DenseNdArray(self._pb_body.values).value = r['values']
        self._pb_body.ClearField('dense_shape')
        self._pb_body.dense_shape.extend(r['shape'])
