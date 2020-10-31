from typing import Type

from . import BaseNdArray
from .dense import BaseDenseNdArray
from .dense.numpy import DenseNdArray
from .sparse import BaseSparseNdArray
from .sparse.scipy import SparseNdArray
from .. import jina_pb2


class GenericNdArray(BaseNdArray):
    def __init__(self, proto: 'jina_pb2.NdArray' = None,
                 is_sparse: bool = False,
                 dense_cls: Type['BaseDenseNdArray'] = DenseNdArray,
                 sparse_cls: Type['BaseSparseNdArray'] = SparseNdArray,
                 *args, **kwargs):
        super().__init__(proto, *args, **kwargs)
        self.is_sparse = is_sparse
        self.dense_cls = dense_cls
        self.sparse_cls = sparse_cls
        self._args = args
        self._kwargs = kwargs

    def null_proto(self):
        return jina_pb2.NdArray()

    @property
    def value(self):
        stype = self.proto.WhichOneof('content')
        if stype == 'dense':
            return self.dense_cls(self.proto.dense).value
        elif stype == 'sparse':
            return self.sparse_cls(self.proto.sparse).value
        else:
            raise ValueError('empty value, this protobuf is probably not initialized yet?')

    @value.setter
    def value(self, value):
        if self.is_sparse:
            self.sparse_cls(self.proto.sparse).value = value
        else:
            self.dense_cls(self.proto.dense).value = value
