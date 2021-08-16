from typing import Tuple, Union, TYPE_CHECKING, Optional

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
    x: Union['np.ndarray', _SPARSE_SCIPY_TYPES],
    t_range: Tuple = (0, 1),
    x_range: Optional[Tuple] = None,
    eps: float = 1e-7,
):
    """Normalize values in `x` into `t_range`.

    `x` can be a 1D array or a 2D array. When `x` is a 2D array, then normalization is row-based.

    .. note::
        - with `t_range=(0, 1)` will normalize the min-value of the data to 0, max to 1;
        - with `t_range=(1, 0)` will normalize the min-value of the data to 1, max value of the data to 0.

    :param x: the data to be normalized
    :param t_range: a tuple represents the target range.
    :param x_range: a tuple represents x range.
    :param eps: a small jitter to avoid divde by zero
    :return: normalized data in `t_range`
    """
    a, b = t_range

    if isinstance(x, np.ndarray):
        min_d = x_range[0] if x_range else np.min(x, axis=-1, keepdims=True)
        max_d = x_range[1] if x_range else np.max(x, axis=-1, keepdims=True)
        r = (b - a) * (x - min_d) / (max_d - min_d + eps) + a
    else:
        min_d = x_range[0] if x_range else x.min(axis=-1).toarray()
        max_d = x_range[1] if x_range else x.max(axis=-1).toarray()
        r = (b - a) * (x - min_d) / (max_d - min_d + eps) + a

    return np.clip(r, *((a, b) if a < b else (b, a)))


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


def update_rows_x_mat_best(
    x_mat_best: 'np.ndarray',
    x_inds_best: 'np.ndarray',
    x_mat: 'np.ndarray',
    x_inds: 'np.ndarray',
    k: int,
):
    """
    Updates `x_mat_best` and `x_inds_best` rows with the k best values and indices (per row)  from `x_mat` union `x_mat_best`.

    :param x_mat: numpy array of the first matrix
    :param x_inds: numpy array of the indices of the first matrix
    :param x_mat_best: numpy array of the second matrix
    :param x_inds_best: numpy array of the indices of the second matrix
    :param k: number of values to retrieve
    :return: indices and distances
    """
    all_dists = np.hstack((x_mat, x_mat_best))
    all_inds = np.hstack((x_inds, x_inds_best))
    best_inds = np.argpartition(all_dists, kth=k, axis=1)
    x_mat_best = np.take_along_axis(all_dists, best_inds, axis=1)[:, :k]
    x_inds_best = np.take_along_axis(all_inds, best_inds, axis=1)[:, :k]
    return x_mat_best, x_inds_best
