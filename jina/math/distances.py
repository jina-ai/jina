import numpy as np


def cosine_distance(x: 'np.ndarray', y: 'np.ndarray') -> 'np.ndarray':
    """Cosine distance between each row in X and each row in Y.
    :param x: np.ndarray with ndim=2
    :param y: np.ndarray with ndim=2
    :return: np.ndarray  with ndim=2
    """
    return 1 - np.dot(x, y.T) / np.outer(
        np.linalg.norm(x, axis=1), np.linalg.norm(y, axis=1)
    )


def euclidean_distance_squared(x: 'np.ndarray', y: 'np.ndarray') -> 'np.ndarray':
    """Euclidean (squared) distance between each row in X and each row in Y.
    :param x: np.ndarray with ndim=2
    :param y: np.ndarray with ndim=2
    :return: np.ndarray with ndim=2
    """
    return (
        np.sum(y ** 2, axis=1)
        + np.sum(x ** 2, axis=1)[:, np.newaxis]
        - 2 * np.dot(x, y.T)
    )


def compute_distances(x: 'np.ndarray', y: 'np.ndarray', metric: str) -> 'np.ndarray':
    """Computes the distance between each row of X and each row on Y according to `metric`.
    - Let `n_X = X.shape[0]`
    - Let `n_Y = Y.shape[0]`
    - Returns a matrix `dist` of shape `(n_X, n_Y)` with `dist[i,j] = metric(X[i], X[j])`.
    :param x: np.ndarray of ndim 2
    :param y:  np.ndarray of ndim 2
    :param metric: string describing the metric type
    :return: np.ndarray of ndim 2
    """
    if metric == 'cosine':
        dists = cosine_distance(x, y)
    elif metric == 'euclidean_squared':
        dists = euclidean_distance_squared(x, y)
    elif metric == 'euclidean':
        dists = np.sqrt(euclidean_distance_squared(x, y))
    else:
        raise ValueError(f'Input metric={metric} not valid')
    return dists
