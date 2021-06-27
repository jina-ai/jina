from typing import List

import numpy as np
import torch
from torch.sparse import FloatTensor

from . import BaseSparseNdArray
from ....proto import jina_pb2

if False:
    import numpy as np

__all__ = ['SparseNdArray']


class SparseNdArray(BaseSparseNdArray):
    """
    Pytorch powered sparse ndarray, i.e. FloatTensor.

    .. seealso::
        https://pytorch.org/docs/stable/sparse.html

    :param proto: protobuf instance, default is None.
    :param transpose_indices: in torch, the input to LongTensor is NOT a list of index tuples.
    :param args: positional arguments.
    :param kwargs: positional key value arguments.

    If you want to write your indices this way, you should transpose before passing them to the sparse constructor

    .. note::
        To comply with Tensorflow, `transpose_indices` is set to True by default
    """

    def __init__(
        self,
        proto: 'jina_pb2.SparseNdArrayProto' = None,
        transpose_indices: bool = True,
        *args,
        **kwargs
    ):
        super().__init__(proto, *args, **kwargs)
        self.transpose_indices = transpose_indices

    def sparse_constructor(
        self, indices: 'np.ndarray', values: 'np.ndarray', shape: List[int]
    ) -> 'FloatTensor':
        """
        Sparse NdArray constructor for FloatTensor.

        :param indices: the indices of the sparse array
        :param values: the values of the sparse array
        :param shape: the shape of the sparse array
        :return: FloatTensor
        """
        return FloatTensor(
            torch.LongTensor(indices).T
            if self.transpose_indices
            else torch.LongTensor(indices),
            torch.FloatTensor(values),
            torch.Size(shape),
        )

    def sparse_parser(self, value: 'FloatTensor'):
        """
        Parse a FloatTensor to indices, values and shape.

        :param value: the FloatTensor.
        :return: a Dict with three entries {'indices': ..., 'values':..., 'shape':...}
        """
        indices = value._indices().numpy()
        if self.transpose_indices:
            indices = indices.T
        values = value._values().numpy()
        shape = list(value.size())
        return {
            'indices': indices,
            'values': values,
            'shape': shape,
        }
