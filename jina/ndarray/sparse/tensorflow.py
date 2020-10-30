from tensorflow import SparseTensor

from .. import BaseNdArray
from ..dense.numpy import DenseNdArray
from ...proto import jina_pb2


class SparseNdArray(BaseNdArray):
    """Scipy powered sparse ndarray

    .. warning::
        scipy only supports ndim=2
    """

    @property
    def value(self) -> 'SparseTensor':
        return SparseTensor(DenseNdArray(self.proto.indicies).value,
                            DenseNdArray(self.proto.values).value,
                            self.proto.dense_shape)

    @value.setter
    def value(self, value: 'SparseTensor'):
        DenseNdArray(self.proto.indicies).value = value.indices.numpy()
        DenseNdArray(self.proto.values).value = value.values.numpy()
        self.proto.dense_shape.extend(value.shape.as_list())

