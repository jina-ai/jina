__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

import numpy as np

from . import BaseNumpyIndexer


class NaiveIndexer(BaseNumpyIndexer):
    """An exhaustive vector indexers implemented with numpy and scipy. """

    def __init__(self, metric: str = 'euclidean',
                 backend: str = 'numpy',
                 *args, **kwargs):
        """
        :param metric: The distance metric to use. `braycurtis`, `canberra`, `chebyshev`, `cityblock`, `correlation`,
                        `cosine`, `dice`, `euclidean`, `hamming`, `jaccard`, `jensenshannon`, `kulsinski`,
                        `mahalanobis`,
                        `matching`, `minkowski`, `rogerstanimoto`, `russellrao`, `seuclidean`, `sokalmichener`,
                        `sokalsneath`, `sqeuclidean`, `wminkowski`, `yule`.
        :param backend: `numpy` or `scipy`, `numpy` only supports `euclidean` and `cosine` distance

        .. note::
            Metrics other than `cosine` and `euclidean` requires ``scipy`` installed.

        """
        super().__init__(*args, **kwargs)
        self.metric = metric
        self.backend = backend

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        """ Find the top-k vectors with smallest ``metric`` and return their ids.

        :return: a tuple of two ndarray.
            The first is ids in shape B x K (`dtype=int`), the second is metric in shape B x K (`dtype=float`)

        .. warning::
            This operation is memory-consuming.

            Distance (the smaller the better) is returned, not the score.

        """
        if self.metric not in {'cosine', 'euclidean'} or self.backend == 'scipy':
            try:
                from scipy.spatial.distance import cdist
                dist = cdist(keys, self.query_handler, metric=self.metric)
            except ModuleNotFoundError:
                self.logger.error(f'your metric {self.metric} requires scipy, but scipy is not found')
        elif self.metric == 'euclidean':
            dist = _euclidean(keys, self.query_handler)
        elif self.metric == 'cosine':
            dist = _cosine(keys, self.query_handler)

        idx = np.argpartition(dist, kth=top_k, axis=1)[:, :top_k]
        dist = np.take_along_axis(dist, idx, axis=1)
        return self.int2ext_key[idx], dist

    def build_advanced_index(self, vecs: 'np.ndarray'):
        return vecs


class NumpyIndexer(NaiveIndexer):
    """Depreciated, will be removed in the future"""


def _ext_arrs(A, B):
    nA, dim = A.shape
    A_ext = np.ones((nA, dim * 3))
    A_ext[:, dim:2 * dim] = A
    A_ext[:, 2 * dim:] = A ** 2

    nB = B.shape[0]
    B_ext = np.ones((dim * 3, nB))
    B_ext[:dim] = (B ** 2).T
    B_ext[dim:2 * dim] = -2.0 * B.T
    return A_ext, B_ext


def _euclidean(A, B):
    A_ext, B_ext = _ext_arrs(A, B)
    sqdist = A_ext.dot(B_ext).clip(min=0)
    return np.sqrt(sqdist)


def _cosine(A, B):
    A_ext, B_ext = _ext_arrs(A / np.linalg.norm(A, ord=2, axis=1, keepdims=True),
                             B / np.linalg.norm(B, ord=2, axis=1, keepdims=True))
    return A_ext.dot(B_ext).clip(min=0) / 2
