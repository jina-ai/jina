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
        """Set constructor method.

        :param args: args passed to super().
        :param kwargs: kwargs passed to super().
        """
        super().__init__(*args, **kwargs)
        self.is_sparse = True

    def null_proto(self) -> 'jina_pb2.SparseNdArrayProto':
        """Get the new protobuf representation.

        :return: An empty `SparseNdArrayProto`
        """
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

        .. # noqa: DAR202
        """
        raise NotImplementedError

    def sparse_parser(
        self, value: AnySparseNdArray
    ) -> Dict[str, Union['np.ndarray', List[int]]]:
        """
        Parse a Sparse NdArray to indices, values and shape, must be implemented by subclass.

        :param value: the sparse ndarray
        :return: a Dict with three entries {'indices': ..., 'values':..., 'shape':...}

        .. # noqa: DAR202
        """
        raise NotImplementedError

    @property
    def value(self) -> AnySparseNdArray:
        """Get the value of protobuf message in :class:`SparseNdArray`.

        :return: A :class:`SparseNdArray`.
        """
        idx = DenseNdArray(self._pb_body.indices).value
        val = DenseNdArray(self._pb_body.values).value
        shape = self._pb_body.shape
        if idx is not None and val is not None and shape:
            return self.sparse_constructor(idx, val, shape)

    @value.setter
    def value(self, value: AnySparseNdArray):
        """Set the value of protobuf message with :param:`value` in :class:`SparseNdArray`.

        :param value: The :class:`SparseNdArray` to be set as the value of the cls.
        """
        r = self.sparse_parser(value)
        DenseNdArray(self._pb_body.indices).value = r['indices']
        DenseNdArray(self._pb_body.values).value = r['values']
        self._pb_body.ClearField('shape')
        self._pb_body.shape.extend(r['shape'])
