import numpy as np

from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    import scipy

_SPARSE_SCIPY_TYPES = Union[
    'scipy.sparse.csr_matrix',
    'scipy.sparse.csc_matrix',
    'scipy.sparse.bsr_matrix',
    'scipy.sparse.coo_matrix',
]


def pdist(
    x_mat: Union['np.ndarray', _SPARSE_SCIPY_TYPES],
    metric: str,
    is_sparse: bool = False,
) -> 'np.ndarray':
    """Computes Pairwise distances between observations in n-dimensional space.

    :param x_mat: Union['np.ndarray','scipy.sparse.csr_matrix', 'scipy.sparse.coo_matrix'] of ndim 2
    :param metric: string describing the metric type
    :param is_sparse: boolean stating if computation must be done with sparse data
    :return: np.ndarray of ndim 2
    """
    return cdist(x_mat, x_mat, metric, is_sparse)


def cdist(
    x_mat: Union['np.ndarray', _SPARSE_SCIPY_TYPES],
    y_mat: Union['np.ndarray', _SPARSE_SCIPY_TYPES],
    metric: str,
    is_sparse: bool = False,
) -> 'np.ndarray':

    """Computes the pairwise distance between each row of X and each row on Y according to `metric`.
    - Let `n_x = x_mat.shape[0]`
    - Let `n_y = y_mat.shape[0]`
    - Returns a matrix `dist` of shape `(n_x, n_y)` with `dist[i,j] = metric(x_mat[i], y_mat[j])`.
    :param x_mat: numpy or scipy array of ndim 2
    :param y_mat: numpy or scipy array of ndim 2
    :param metric: string describing the metric type
    :param is_sparse: boolean describing if data type is sparse
    :return: np.ndarray of ndim 2
    """
    if metric == 'cosine':
        if is_sparse:
            dists = sparse_cosine(x_mat, y_mat)
        else:
            dists = cosine(x_mat, y_mat)

    elif metric == 'sqeuclidean':
        if is_sparse:
            dists = sparse_sqeuclidean(x_mat, y_mat)
        else:
            dists = sqeuclidean(x_mat, y_mat)

    elif metric == 'euclidean':
        if is_sparse:
            dists = np.sqrt(sparse_sqeuclidean(x_mat, y_mat))
        else:
            dists = np.sqrt(sqeuclidean(x_mat, y_mat))
    else:
        raise ValueError(f'Input metric={metric} not valid')
    return dists


def cosine(x_mat: 'np.ndarray', y_mat: 'np.ndarray', eps: float = 1e-7) -> 'np.ndarray':
    """Cosine distance between each row in x_mat and each row in y_mat.
    :param x_mat: np.ndarray with ndim=2
    :param y_mat: np.ndarray with ndim=2
    :param eps: a small jitter to avoid divde by zero
    :return: np.ndarray  with ndim=2
    """
    return 1 - np.clip(
        (np.dot(x_mat, y_mat.T) + eps)
        / (
            np.outer(np.linalg.norm(x_mat, axis=1), np.linalg.norm(y_mat, axis=1)) + eps
        ),
        -1,
        1,
    )


def sqeuclidean(x_mat: 'np.ndarray', y_mat: 'np.ndarray') -> 'np.ndarray':
    """squared Euclidean distance between each row in x_mat and each row in y_mat.
    :param x_mat: np.ndarray with ndim=2
    :param y_mat: np.ndarray with ndim=2
    :return: np.ndarray with ndim=2
    """
    return (
        np.sum(y_mat ** 2, axis=1)
        + np.sum(x_mat ** 2, axis=1)[:, np.newaxis]
        - 2 * np.dot(x_mat, y_mat.T)
    )


def sparse_cosine(
    x_mat: _SPARSE_SCIPY_TYPES, y_mat: _SPARSE_SCIPY_TYPES
) -> 'np.ndarray':
    """Cosine distance between each row in x_mat and each row in y_mat.
    :param x_mat:  scipy.sparse like array with ndim=2
    :param y_mat:  scipy.sparse like array with ndim=2
    :return: np.ndarray  with ndim=2
    """
    from scipy.sparse.linalg import norm

    # we need the np.asarray otherwise we get a np.matrix object that iterates differently
    return 1 - np.clip(
        np.asarray(
            x_mat.dot(y_mat.T) / (np.outer(norm(x_mat, axis=1), norm(y_mat, axis=1)))
        ),
        -1,
        1,
    )


def sparse_sqeuclidean(
    x_mat: _SPARSE_SCIPY_TYPES, y_mat: _SPARSE_SCIPY_TYPES
) -> 'np.ndarray':
    """Cosine distance between each row in x_mat and each row in y_mat.
    :param x_mat:  scipy.sparse like array with ndim=2
    :param y_mat:  scipy.sparse like array with ndim=2
    :return: np.ndarray  with ndim=2
    """
    # we need the np.asarray otherwise we get a np.matrix object that iterates differently
    return np.asarray(
        y_mat.power(2).sum(axis=1).flatten()
        + x_mat.power(2).sum(axis=1)
        - 2 * x_mat.dot(y_mat.T)
    )
