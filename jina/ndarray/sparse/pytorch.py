import torch
from torch.sparse import FloatTensor

from .. import BaseSparseNdArray
from ..dense.numpy import DenseNdArray


class SparseNdArray(BaseSparseNdArray):
    """Pytorch powered sparse ndarray, i.e. FloatTensor
    """

    @property
    def value(self) -> 'FloatTensor':
        return FloatTensor(torch.LongTensor(DenseNdArray(self.proto.indicies).value),
                           torch.FloatTensor(DenseNdArray(self.proto.values).value),
                           torch.Size(self.proto.dense_shape))

    @value.setter
    def value(self, value: 'FloatTensor'):
        DenseNdArray(self.proto.indicies).value = value._indices().numpy()
        DenseNdArray(self.proto.values).value = value._values().numpy()
        self.proto.dense_shape.extend(list(value.shape))
