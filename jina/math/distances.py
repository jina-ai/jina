import numpy as np


def cosine_distance(x_mat: 'np.ndarray', y_mat: 'np.ndarray') -> 'np.ndarray':
    """Cosine distance between each row in x_mat and each row in y_mat.
    :param x_mat: np.ndarray with ndim=2
    :param y_mat: np.ndarray with ndim=2
    :return: np.ndarray  with ndim=2
    """
    return 1 - np.dot(x_mat, y_mat.T) / np.outer(
        np.linalg.norm(x_mat, axis=1), np.linalg.norm(y_mat, axis=1)
    )


def euclidean_distance_squared(
    x_mat: 'np.ndarray', y_mat: 'np.ndarray'
) -> 'np.ndarray':
    """Euclidean (squared) distance between each row in x_mat and each row in y_mat.
    :param x_mat: np.ndarray with ndim=2
    :param y_mat: np.ndarray with ndim=2
    :return: np.ndarray with ndim=2
    """
    return (
        np.sum(y_mat ** 2, axis=1)
        + np.sum(x_mat ** 2, axis=1)[:, np.newaxis]
        - 2 * np.dot(x_mat, y_mat.T)
    )


def compute_distances(
    x_mat: 'np.ndarray', y_mat: 'np.ndarray', metric: str
) -> 'np.ndarray':
    """Computes the distance between each row of X and each row on Y according to `metric`.
    - Let `n_x = x_mat.shape[0]`
    - Let `n_y = y_mat.shape[0]`
    - Returns a matrix `dist` of shape `(n_x, n_y)` with `dist[i,j] = metric(x_mat[i], x_mat[j])`.
    :param x_mat: np.ndarray of ndim 2
    :param y_mat:  np.ndarray of ndim 2
    :param metric: string describing the metric type
    :return: np.ndarray of ndim 2
    """
    if metric == 'cosine':
        dists = cosine_distance(x_mat, y)
    elif metric == 'euclidean_squared':
        dists = euclidean_distance_squared(x_mat, y)
    elif metric == 'euclidean':
        dists = np.sqrt(euclidean_distance_squared(x_mat, y))
    else:
        raise ValueError(f'Input metric={metric} not valid')
    return dists
