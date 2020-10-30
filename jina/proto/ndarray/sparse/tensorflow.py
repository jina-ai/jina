from tensorflow import SparseTensor

from .. import BaseSparseNdArray
from ..dense.numpy import DenseNdArray


class SparseNdArray(BaseSparseNdArray):
    """Tensorflow powered sparse ndarray, i.e. SparseTensor
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
