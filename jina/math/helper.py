from typing import Tuple

import numpy as np


def minmax_normalize(x: 'np.ndarray', t_range: Tuple = (0, 1)):
    """Normalize values in `x` into `t_range`.

    `x` can be a 1D array or a 2D array. When `x` is a 2D array, then normalization is row-based.

    .. note::
        - with `t_range=(0, 1)` will normalize the min-value of the data to 0, max to 1;
        - with `t_range=(1, 0)` will normalize the min-value of the data to 1, max value of the data to 0.

    :param x: the data to be normalized
    :param t_range: a tuple represents the target range.
    :return: normalized data in `t_range`
    """
    min_d = np.min(x, axis=-1, keepdims=True)
    max_d = np.max(x, axis=-1, keepdims=True)
    a, b = t_range
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


def top_k_from_pair(
    x_mat: 'np.ndarray',
    x_inds: 'np.ndarray',
    y_mat: 'np.ndarray',
    y_inds: 'np.ndarray',
    k: int,
) -> Tuple['np.ndarray', 'np.ndarray']:
    """
    Finds values and indices of the k largest entries found in `x_ma` union `y_mat`
    and the indices from `x_inds` union `y_inds`

    :param x_mat: numpy array of the first matrix
    :param x_inds: numpy array of the indices of the first matrix
    :param y_mat: numpy array of the second matrix
    :param y_inds: numpy array of the indices of the second matrix
    :param k: number of values to retrieve
    :return: indices and distances of the best items in the pair
    """
    all_dists = np.hstack((x_mat, y_mat))
    all_inds = np.hstack((x_inds, y_inds))
    best_inds = np.argpartition(all_dists, kth=k, axis=1)
    d_mat = np.take_along_axis(all_dists, best_inds, axis=1)
    i_mat = np.take_along_axis(all_inds, best_inds, axis=1)
    return d_mat[:, :k], i_mat[:, :k]
