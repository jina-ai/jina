from math import inf
from typing import Optional, Union, Callable, Tuple

import numpy as np

from jina import Document
from ...math.helper import top_k, minmax_normalize

if False:
    from .document import DocumentArray
    from .memmap import DocumentArrayMemmap


class DocumentArrayNeuralOpsMixin:
    """ A mixin that provides match functionality to DocumentArrays """

    def match(
        self,
        darray: Union['DocumentArray', 'DocumentArrayMemmap'],
        metric: Union[
            str, Callable[['np.ndarray', 'np.ndarray'], 'np.ndarray']
        ] = 'cosine',
        limit: Optional[int] = inf,
        normalization: Optional[Tuple[int, int]] = None,
        use_scipy: bool = False,
        metric_name: Optional[str] = None,
    ) -> None:
        """Compute embedding based nearest neighbour in `another` for each Document in `self`,
        and store results in `matches`.

        .. note::
            'cosine', 'euclidean', 'sqeuclidean' are supported natively without extra dependency.

            You can use other distance metric provided by ``scipy``, such as ‘braycurtis’, ‘canberra’, ‘chebyshev’,
            ‘cityblock’, ‘correlation’, ‘cosine’, ‘dice’, ‘euclidean’, ‘hamming’, ‘jaccard’, ‘jensenshannon’,
            ‘kulsinski’, ‘mahalanobis’, ‘matching’, ‘minkowski’, ‘rogerstanimoto’, ‘russellrao’, ‘seuclidean’,
            ‘sokalmichener’, ‘sokalsneath’, ‘sqeuclidean’, ‘wminkowski’, ‘yule’.

            To use scipy metric, please set ``use_scipy=True``.

        - To make all matches values in [0, 1], use ``dA.match(dB, normalization=(0, 1))``
        - To invert the distance as score and make all values in range [0, 1],
            use ``dA.match(dB, normalization=(1, 0))``. Note, how ``normalization`` differs from the previous.

        :param darray: the other DocumentArray or DocumentArrayMemmap to match against
        :param metric: the distance metric
        :param limit: the maximum number of matches, when not given
                      all Documents in `another` are considered as matches
        :param normalization: a tuple [a, b] to be used with min-max normalization,
                                the min distance will be rescaled to `a`, the max distance will be rescaled to `b`
                                all values will be rescaled into range `[a, b]`.
        :param use_scipy: use Scipy as the computation backend
        :param metric_name: if provided, then match result will be marked with this string.
        """

        X = np.stack(self.get_attributes('embedding'))
        Y = np.stack(darray.get_attributes('embedding'))
        limit = min(limit, len(darray))

        if isinstance(metric, str):
            if use_scipy:
                from scipy.spatial.distance import cdist
            else:
                from ...math.distance import cdist
            dists = cdist(X, Y, metric)
        elif callable(metric):
            dists = metric(X, Y)
        else:
            raise TypeError(
                f'metric must be either string or a 2-arity function, received: {metric!r}'
            )

        dist, idx = top_k(dists, limit, descending=False)
        if normalization is not None:
            if isinstance(normalization, (tuple, list)):
                dist = minmax_normalize(dist, normalization)

        m_name = metric_name or (metric.__name__ if callable(metric) else metric)
        for _q, _ids, _dists in zip(self, idx, dist):
            _q.matches.clear()
            for _id, _dist in zip(_ids, _dists):
                d = Document(darray[int(_id)], copy=True)
                d.scores[m_name] = _dist
                _q.matches.append(d)
