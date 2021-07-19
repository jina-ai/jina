from math import inf
from typing import Optional, Tuple

import numpy as np

from jina import Document

if False:
    from .document import DocumentArrayGetAttrMixin


class DocumentArrayNeuralOperationsMixin:
    """ A mixin that provides match functionality to DocumentArrays """

    def match(
        self,
        darray: 'DocumentArrayGetAttrMixin',
        metric: str = 'cosine',
        limit: Optional[int] = inf,
        is_distance: bool = False,
    ) -> None:
        """Compute embedding based nearest neighbour in `another` for each Document in `self`,
        and store results in `matches`.

        Note:
            - If metric is 'cosine' it uses the cosine **distance**.
            - If metric is 'euclidean' it uses the euclidean **distance**.
            - If metric is 'euclidean_squared' it uses the euclidean **distance** squared.

        :param darray: the other DocumentArray to match against
        :param metric: the distance metric
        :param limit: the maximum number of matches, when not given
                      all Documents in `another` are considered as matches
        :param is_distance: Boolean flag informing if `metric` values want to be considered as distances or scores.
        """

        def invert_if_score(
            X: 'np.ndarray', metric: str, is_distance: bool
        ) -> 'np.ndarray':
            """Invert values to scores if `is_distance=False` according to the metric that is passed.

            :param X: input np.ndarray
            :param metric: string defining distance function ['cosine', 'euclidean', euclidean_squared'].
            :param is_distance: Boolean flag that describes if values in X need to be reinterpreted as similarities.
            :return: A np.ndarray with distances if `is_distance=True`, scores if distance=False`.
            """
            if metric == 'cosine':
                if is_distance:
                    X = X
                else:
                    X = 1 - X
            if metric == 'euclidean_squared' or metric == 'euclidean':
                if is_distance:
                    X = X
                else:
                    X = 1 / (X + 1)
            return X

        X = np.stack(self.get_attributes('embedding'))
        Y = np.stack(darray.get_attributes('embedding'))
        limit = min(limit, len(darray))

        dists = compute_distances(X, Y, metric)
        idx, dist = self._get_sorted_smallest_k(dists, limit)

        for _q, _ids, _dists in zip(self, idx, dist):
            for _id, _dist in zip(_ids, _dists):
                d = Document(darray[int(_id)], copy=True)
                d.scores[metric] = invert_if_score(_dist, metric, is_distance)
                _q.matches.append(d)

    @staticmethod
    def _get_sorted_smallest_k(
        dists: 'np.ndarray', top_k: int
    ) -> Tuple['np.ndarray', 'np.ndarray']:
        """Finds the smallest `top_k` values (and its indices) from `dists`. Returns both indices and values.

        :param dists: np.ndarray of distances
        :param top_k: number of values to retrieve
        :return: Lowest values in dists and the indices of those values
        """
        if top_k >= dists.shape[1]:
            indices = dists.argsort(axis=1)[:, :top_k]
            dists = np.take_along_axis(dists, indices, axis=1)
        else:
            indices_ps = dists.argpartition(kth=top_k, axis=1)[:, :top_k]
            dists = np.take_along_axis(dists, indices_ps, axis=1)
            indices_fs = dists.argsort(axis=1)
            indices = np.take_along_axis(indices_ps, indices_fs, axis=1)
            dists = np.take_along_axis(dists, indices_fs, axis=1)

        return indices, dists


def compute_distances(X: 'np.ndarray', Y: 'np.ndarray', metric: str) -> 'np.ndarray':
    """Computes the distance between each row of X and each row on Y according to `metric`.
    - Let `n_X = X.shape[0]`
    - Let `n_Y = Y.shape[0]`
    - Returns a matrix `dist` of shape `(n_X, n_Y)` with `dist[i,j] = metric(X[i], X[j])`.
    :param X: np.ndarray of ndim 2
    :param Y:  np.ndarray of ndim 2
    :param metric: string describing the metric type
    :return: np.ndarray of ndim 2
    """
    assert metric in [
        'cosine',
        'euclidean_squared',
        'euclidean',
    ], f'Input metric={metric} not valid'
    if metric == 'cosine':
        dists = cosine_distance(X, Y)
    if metric == 'euclidean_squared':
        dists = euclidean_distance_squared(X, Y)
    if metric == 'euclidean':
        dists = np.sqrt(euclidean_distance_squared(X, Y))
    return dists


def cosine_distance(X: 'np.ndarray', Y: 'np.ndarray') -> 'np.ndarray':
    """Cosine distance between each row in X and each row in Y.
    :param X: np.ndarray with ndim=2
    :param Y: np.ndarray with ndim=2
    :return: np.ndarray  with ndim=2
    """
    return 1 - np.dot(X, Y.T) / np.outer(
        np.linalg.norm(X, axis=1), np.linalg.norm(Y, axis=1)
    )


def euclidean_distance_squared(X: 'np.ndarray', Y: 'np.ndarray') -> 'np.ndarray':
    """Euclidean (squared) distance between each row in X and each row in Y.
    :param X: np.ndarray with ndim=2
    :param Y: np.ndarray with ndim=2
    :return: np.ndarray with ndim=2
    """
    return (
        np.sum(Y ** 2, axis=1)
        + np.sum(X ** 2, axis=1)[:, np.newaxis]
        - 2 * np.dot(X, Y.T)
    )
