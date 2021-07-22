from math import inf
from typing import Optional, Tuple, Union

import numpy as np

from jina import Document

if False:
    from .document import DocumentArray
    from .memmap import DocumentArrayMemmap


class DocumentArrayNeuralOpsMixin:
    """ A mixin that provides match functionality to DocumentArrays """

    def match(
        self,
        darray: Union['DocumentArray', 'DocumentArrayMemmap'],
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

        :param darray: the other DocumentArray or DocumentArrayMemmap to match against
        :param metric: the distance metric
        :param limit: the maximum number of matches, when not given
                      all Documents in `another` are considered as matches
        :param is_distance: Boolean flag informing if `metric` values want to be considered as distances or scores.
        """

        def invert_if_score(
            x: 'np.ndarray',
        ) -> 'np.ndarray':
            """Invert values to scores if `is_distance=False` according to the metric that is passed.

            :param x: input np.ndarray
            :return: A np.ndarray with distances if `is_distance=True`, scores if distance=False`.
            """
            if metric == 'cosine':
                if is_distance:
                    x = x
                else:
                    x = 1 - x
            elif metric == 'euclidean_squared' or metric == 'euclidean':
                if is_distance:
                    x = x
                else:
                    x = 1 / (x + 1)
            return x

        X = np.stack(self.get_attributes('embedding'))
        Y = np.stack(darray.get_attributes('embedding'))
        limit = min(limit, len(darray))

        dists = _compute_distances(X, Y, metric)
        idx, dist = self._get_sorted_smallest_k(dists, limit)
        dist = invert_if_score(dist)

        for _q, _ids, _dists in zip(self, idx, dist):
            for _id, _dist in zip(_ids, _dists):
                d = Document(darray[int(_id)], copy=True)
                d.scores[metric] = _dist
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


def _compute_distances(x: 'np.ndarray', y: 'np.ndarray', metric: str) -> 'np.ndarray':
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
        dists = _cosine_distance(x, y)
    elif metric == 'euclidean_squared':
        dists = _euclidean_distance_squared(x, y)
    elif metric == 'euclidean':
        dists = np.sqrt(_euclidean_distance_squared(x, y))
    else:
        raise ValueError(f'Input metric={metric} not valid')
    return dists


def _cosine_distance(x: 'np.ndarray', y: 'np.ndarray') -> 'np.ndarray':
    """Cosine distance between each row in X and each row in Y.
    :param x: np.ndarray with ndim=2
    :param y: np.ndarray with ndim=2
    :return: np.ndarray  with ndim=2
    """
    return 1 - np.dot(x, y.T) / np.outer(
        np.linalg.norm(x, axis=1), np.linalg.norm(y, axis=1)
    )


def _euclidean_distance_squared(x: 'np.ndarray', y: 'np.ndarray') -> 'np.ndarray':
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
