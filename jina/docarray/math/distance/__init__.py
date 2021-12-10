from typing import TYPE_CHECKING

from ...ndarray import get_array_type

if TYPE_CHECKING:
    from ...ndarray import ArrayType
    import numpy as np


def pdist(
    x_mat: 'ArrayType',
    metric: str,
) -> 'np.ndarray':
    """Computes Pairwise distances between observations in n-dimensional space.

    :param x_mat: Union['np.ndarray','scipy.sparse.csr_matrix', 'scipy.sparse.coo_matrix'] of ndim 2
    :param metric: string describing the metric type
    :return: np.ndarray of ndim 2
    """
    return cdist(x_mat, x_mat, metric)


def cdist(
    x_mat: 'ArrayType', y_mat: 'ArrayType', metric: str, device: str = 'cpu'
) -> 'np.ndarray':
    """Computes the pairwise distance between each row of X and each row on Y according to `metric`.
    - Let `n_x = x_mat.shape[0]`
    - Let `n_y = y_mat.shape[0]`
    - Returns a matrix `dist` of shape `(n_x, n_y)` with `dist[i,j] = metric(x_mat[i], y_mat[j])`.
    :param x_mat: numpy or scipy array of ndim 2
    :param y_mat: numpy or scipy array of ndim 2
    :param metric: string describing the metric type
    :param device: the computational device, can be either `cpu` or `cuda`.
    :return: np.ndarray of ndim 2
    """

    x_type = get_array_type(x_mat)
    y_type = get_array_type(y_mat)

    if x_type != y_type:
        raise ValueError(
            f'The type of your left-hand side is {x_type}, whereas your right-hand side is {y_type}. '
            f'`.match()` requires left must be the same type as right.'
        )

    framework, is_sparse = get_array_type(x_mat)

    dists = None
    if metric == 'cosine':
        if framework == 'scipy' and is_sparse:
            from .numpy import sparse_cosine

            dists = sparse_cosine(x_mat, y_mat)
        elif framework == 'numpy':
            from .numpy import cosine

            dists = cosine(x_mat, y_mat)
        elif framework == 'tensorflow':
            from .tensorflow import cosine

            dists = cosine(x_mat, y_mat, device=device)
        elif framework == 'torch':
            from .torch import cosine

            dists = cosine(x_mat, y_mat, device=device)
        elif framework == 'paddle':
            from .paddle import cosine

            dists = cosine(x_mat, y_mat, device=device)

    elif metric == 'sqeuclidean':
        if framework == 'scipy' and is_sparse:
            from .numpy import sparse_sqeuclidean

            dists = sparse_sqeuclidean(x_mat, y_mat)
        elif framework == 'numpy':
            from .numpy import sqeuclidean

            dists = sqeuclidean(x_mat, y_mat)
        elif framework == 'tensorflow':
            from .tensorflow import sqeuclidean

            dists = sqeuclidean(x_mat, y_mat, device=device)
        elif framework == 'torch':
            from .torch import sqeuclidean

            dists = sqeuclidean(x_mat, y_mat, device=device)
        elif framework == 'paddle':
            from .paddle import sqeuclidean

            dists = sqeuclidean(x_mat, y_mat, device=device)

    elif metric == 'euclidean':
        if framework == 'scipy' and is_sparse:
            from .numpy import sparse_euclidean

            dists = sparse_euclidean(x_mat, y_mat)
        elif framework == 'numpy':
            from .numpy import euclidean

            dists = euclidean(x_mat, y_mat)
        elif framework == 'tensorflow':
            from .tensorflow import euclidean

            dists = euclidean(x_mat, y_mat, device=device)
        elif framework == 'torch':
            from .torch import euclidean

            dists = euclidean(x_mat, y_mat, device=device)
        elif framework == 'paddle':
            from .paddle import euclidean

            dists = euclidean(x_mat, y_mat, device=device)
    else:
        raise NotImplementedError(f'Input metric={metric} is not supported')

    if dists is None:
        raise NotImplementedError(
            f'{framework} sparse={is_sparse} array is not supported'
        )
    return dists
