from typing import List

import torch
from torch.sparse import FloatTensor

from . import BaseSparseNdArray

if False:
    import numpy as np

__all__ = ['SparseNdArray']


class SparseNdArray(BaseSparseNdArray):
    """Pytorch powered sparse ndarray, i.e. FloatTensor

    .. seealso::
        https://pytorch.org/docs/stable/sparse.html
    """

    def __init__(self, transpose_indices: bool = True, *args, **kwargs):
        """
        :param transpose_indices: in torch, the input to LongTensor is NOT a list of index tuples.
        If you want to write your indices this way, you should transpose before passing them to the sparse constructor

        .. note::
            To comply with Tensorflow, `transpose_indices` is set to True by default
        """
        super().__init__(*args, **kwargs)
        self.transpose_indices = transpose_indices

    def sparse_constructor(self, indices: 'np.ndarray', values: 'np.ndarray', shape: List[int]) -> 'FloatTensor':
        return FloatTensor(torch.LongTensor(indices).T if self.transpose_indices else torch.LongTensor(indices),
                           torch.FloatTensor(values),
                           torch.Size(shape))

    def sparse_parser(self, value: 'FloatTensor'):
        indices = value._indices().numpy()
        if self.transpose_indices:
            indices = indices.T
        return {'indices': indices,
                'values': value._values().numpy(),
                'shape': list(value.shape)}
