from math import inf
from typing import Optional, Union, Callable, Tuple
from itertools import cycle

import numpy as np

from jina import Document
from ...math.helper import top_k, minmax_normalize
from ...math.dimensionality_reduction import PCA

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
                # Note, when match self with other, or both of them share the same Document
                # we might have recursive matches .
                # checkout https://github.com/jina-ai/jina/issues/3034
                d = darray[int(_id)]
                if d.id in self:
                    d.pop('matches')
                _q.matches.append(d, scores={m_name: _dist}, copy=False)

    def visualize(
        self,
        tag_name: Union[str, None] = None,
        file_path: Union[None, str] = None,
        alpha: float = 0.2,
    ):
        """Visualize embeddings in a 2D projection with the PCA algorithm.

        If `tag_name` is provided the plot uses a distinct color for each unique tag value in the
        documents of the DocumentArray.

        :param tag_name: Optional str that specifies tag used to color the plot
        :param file_path: Optional path to store the visualization.
        :param alpha: Float in [0,1] defining transparency of the dots in the plot.
                      Value 0 is invisible, value 1 is opaque.
        """

        import matplotlib.pyplot as plt

        color_space = cycle('vbgrcmk')

        pca = PCA(n_components=2)
        x_mat = np.stack(self.get_attributes('embedding'))
        assert isinstance(
            x_mat, np.ndarray
        ), f'Type {type(x_mat)} not currently supported, use np.ndarray embeddings'

        if tag_name:
            tags = [x[tag_name] for x in self.get_attributes('tags')]
            tag_to_num = {tag: num for num, tag in enumerate(set(tags))}
            colors = np.array([tag_to_num[ni] for ni in tags])
        else:
            colors = None

        x_mat_2d = pca.fit_transform(x_mat)
        plt.figure(figsize=(8, 8))
        plt.title(f'{len(x_mat)} documents with PCA')

        if colors is not None:
            # make one plot per color with the correct tag
            for tag in tag_to_num:
                num = tag_to_num[tag]
                x_mat_subset = x_mat_2d[colors == num]
                plt.scatter(
                    x_mat_subset[:, 0],
                    x_mat_subset[:, 1],
                    alpha=alpha,
                    label=f'{tag_name}={tag}',
                )
        else:
            plt.scatter(x_mat_2d[:, 0], x_mat_2d[:, 1], alpha=alpha)

        plt.legend()

        if file_path:
            plt.savefig(file_path)
