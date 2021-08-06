from typing import Tuple, Union, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import scipy

_SPARSE_SCIPY_TYPES = Union[
    'scipy.sparse.csr_matrix',
    'scipy.sparse.csc_matrix',
    'scipy.sparse.bsr_matrix',
    'scipy.sparse.coo_matrix',
]


def minmax_normalize(
    x: Union['np.ndarray', _SPARSE_SCIPY_TYPES], t_range: Tuple = (0, 1)
):
    """Normalize values in `x` into `t_range`.

    `x` can be a 1D array or a 2D array. When `x` is a 2D array, then normalization is row-based.

    .. note::
        - with `t_range=(0, 1)` will normalize the min-value of the data to 0, max to 1;
        - with `t_range=(1, 0)` will normalize the min-value of the data to 1, max value of the data to 0.

    :param x: the data to be normalized
    :param t_range: a tuple represents the target range.
    :return: normalized data in `t_range`
    """
    a, b = t_range

    if isinstance(x, np.ndarray):
        min_d = np.min(x, axis=-1, keepdims=True)
        max_d = np.max(x, axis=-1, keepdims=True)
        return (b - a) * (x - min_d) / (max_d - min_d) + a
    else:
        min_d = x.min(axis=-1).toarray()
        max_d = x.max(axis=-1).toarray()
        return (b - a) * (x - min_d) / (max_d - min_d) + a


def top_k(
    values: 'np.ndarray', k: int, descending: bool = False
) -> Tuple['np.ndarray', 'np.ndarray']:
    """Finds values and indices of the k largest entries for the last dimension.

    :param values: array of distances
    :param k: number of values to retrieve
    :param descending: find top k biggest values
    :return: indices and distances
    """
    if descending:
        values = -values

    if k >= values.shape[1]:
        idx = values.argsort(axis=1)[:, :k]
        values = np.take_along_axis(values, idx, axis=1)
    else:
        idx_ps = values.argpartition(kth=k, axis=1)[:, :k]
        values = np.take_along_axis(values, idx_ps, axis=1)
        idx_fs = values.argsort(axis=1)
        idx = np.take_along_axis(idx_ps, idx_fs, axis=1)
        values = np.take_along_axis(values, idx_fs, axis=1)

    if descending:
        values = -values

    return values, idx
