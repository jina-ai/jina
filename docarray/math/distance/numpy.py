from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ...ndarray import ArrayType


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
    """Squared Euclidean distance between each row in x_mat and each row in y_mat.
    :param x_mat: np.ndarray with ndim=2
    :param y_mat: np.ndarray with ndim=2
    :return: np.ndarray with ndim=2
    """
    return (
        np.sum(y_mat ** 2, axis=1)
        + np.sum(x_mat ** 2, axis=1)[:, np.newaxis]
        - 2 * np.dot(x_mat, y_mat.T)
    )


def sparse_cosine(x_mat: 'ArrayType', y_mat: 'ArrayType') -> 'np.ndarray':
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


def sparse_sqeuclidean(x_mat: 'ArrayType', y_mat: 'ArrayType') -> 'np.ndarray':
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


def sparse_euclidean(x_mat: 'ArrayType', y_mat: 'ArrayType') -> 'np.ndarray':
    """Sparse euclidean distance between each row in x_mat and each row in y_mat.

    :param x_mat:  scipy.sparse like array with ndim=2
    :param y_mat:  scipy.sparse like array with ndim=2
    :return: np.ndarray  with ndim=2
    """
    return np.sqrt(sparse_sqeuclidean(x_mat, y_mat))


def euclidean(x_mat: 'ArrayType', y_mat: 'ArrayType') -> 'np.ndarray':
    """Euclidean distance between each row in x_mat and each row in y_mat.

    :param x_mat:  scipy.sparse like array with ndim=2
    :param y_mat:  scipy.sparse like array with ndim=2
    :return: np.ndarray  with ndim=2
    """
    return np.sqrt(sqeuclidean(x_mat, y_mat))
