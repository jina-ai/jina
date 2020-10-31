from typing import List, Tuple

import torch
from torch.sparse import FloatTensor

from . import BaseSparseNdArray

if False:
    import numpy as np


class SparseNdArray(BaseSparseNdArray):
    """Pytorch powered sparse ndarray, i.e. FloatTensor
    """

    def sparse_constructor(self, indices: 'np.ndarray', values: 'np.ndarray', shape: List[int]) -> 'FloatTensor':
        return FloatTensor(torch.LongTensor(indices),
                           torch.FloatTensor(values),
                           torch.Size(shape))

    def sparse_parser(self, value: 'FloatTensor') -> Tuple['np.ndarray', 'np.ndarray', List[int]]:
        return value._indices().numpy(), value._values().numpy(), list(value.shape)
