from typing import List, Tuple, TypeVar

from ... import jina_pb2
from .. import BaseNdArray
from ..dense.numpy import DenseNdArray

AnySparseNdArray = TypeVar('AnySparseNdArray')

if False:
    import numpy as np


class BaseSparseNdArray(BaseNdArray):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_sparse = True

    def null_proto(self):
        return jina_pb2.SparseNdArray()

    def sparse_constructor(self, indices: 'np.ndarray', values: 'np.ndarray', shape: List[int]) -> AnySparseNdArray:
        raise NotImplementedError

    def sparse_parser(self, value: AnySparseNdArray) -> Tuple['np.ndarray', 'np.ndarray', List[int]]:
        raise NotImplementedError

    @property
    def value(self) -> AnySparseNdArray:
        idx = DenseNdArray(self.proto.indices).value
        val = DenseNdArray(self.proto.values).value
        shape = self.proto.dense_shape
        if idx is not None and val is not None and shape:
            return self.sparse_constructor(idx, val, shape)

    @value.setter
    def value(self, value: AnySparseNdArray):
        ind, val, shape = self.sparse_parser(value)
        DenseNdArray(self.proto.indices).value = ind
        DenseNdArray(self.proto.values).value = val
        self.proto.dense_shape.extend(val)
