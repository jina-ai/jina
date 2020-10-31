from typing import List, TypeVar, Union, Dict

from .. import BaseNdArray
from ..dense.numpy import DenseNdArray
from ... import jina_pb2

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

    def sparse_parser(self, value: AnySparseNdArray) -> Dict[str, Union['np.ndarray', List[int]]]:
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
        r = self.sparse_parser(value)
        DenseNdArray(self.proto.indices).value = r['indices']
        DenseNdArray(self.proto.values).value = r['values']
        self.proto.dense_shape.extend(r['shape'])
