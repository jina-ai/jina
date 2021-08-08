from math import inf
from typing import Optional, Union, Callable, Tuple

import numpy as np

from ... import Document
from ...importer import ImportExtensions
from ...math.helper import top_k, minmax_normalize
from ...logging.predefined import default_logger

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
        is_sparse = False

        if isinstance(darray[0].embedding, np.ndarray):
            X = np.stack(self.get_attributes('embedding'))
            Y = np.stack(darray.get_attributes('embedding'))
        else:
            import scipy.sparse as sp

            if sp.issparse(darray[0].embedding):
                X = sp.vstack(self.get_attributes('embedding'))
                Y = sp.vstack(darray.get_attributes('embedding'))
                is_sparse = True

        limit = min(limit, len(darray))
        if isinstance(metric, str):

            if use_scipy and is_sparse is False:
                # cdist from scipy does not support sparse arrays
                from scipy.spatial.distance import cdist

                dists = cdist(X, Y, metric)
            else:
                if use_scipy:
                    default_logger.info(
                        f'Scipy cdist does not support sparse arrays, using Jina.math.distances sparse cdist'
                    )
                from ...math.distance import cdist

                dists = cdist(X, Y, metric, is_sparse=is_sparse)

        elif callable(metric):
            dists = metric(X, Y)
        else:
            raise TypeError(
                f'metric must be either string or a 2-arity function, received: {metric!r}'
            )

        dist, idx = top_k(dists, min(limit, len(darray)), descending=False)

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
                    d = Document(d, copy=True)
                    d.pop('matches')
                _q.matches.append(d, scores={m_name: _dist}, copy=False)

    def visualize(
        self,
        output: Optional[str] = None,
        title: Optional[str] = None,
        colored_tag: Optional[str] = None,
        colormap: str = 'rainbow',
        method: str = 'pca',
        show_axis: bool = False,
    ):
        """Visualize embeddings in a 2D projection with the PCA algorithm. This function requires ``matplotlib`` installed.

        If `tag_name` is provided the plot uses a distinct color for each unique tag value in the
        documents of the DocumentArray.

        :param output: Optional path to store the visualization. If not given, show in UI
        :param title: Optional title of the plot. When not given, the default title is used.
        :param colored_tag: Optional str that specifies tag used to color the plot
        :param colormap: the colormap string supported by matplotlib.
        :param method: the visualization method, available `pca`, `tsne`. `pca` is fast but may not well represent
                nonlinear relationship of high-dimensional data. `tsne` requires scikit-learn to be installed and is
                much slower.
        :param show_axis: If set, axis and bounding box of the plot will be printed.

        """

        x_mat = np.stack(self.get_attributes('embedding'))
        assert isinstance(
            x_mat, np.ndarray
        ), f'Type {type(x_mat)} not currently supported, use np.ndarray embeddings'

        if method == 'tsne':
            from sklearn.manifold import TSNE

            x_mat_2d = TSNE(n_components=2).fit_transform(x_mat)
        else:
            from ...math.dimensionality_reduction import PCA

            x_mat_2d = PCA(n_components=2).fit_transform(x_mat)

        plt_kwargs = {
            'x': x_mat_2d[:, 0],
            'y': x_mat_2d[:, 1],
            'alpha': 0.2,
            'marker': '.',
        }

        with ImportExtensions(required=True):
            import matplotlib.pyplot as plt

        plt.figure(figsize=(8, 8))
        plt.title(title or f'{len(x_mat)} Documents with PCA')

        if colored_tag:
            tags = [x[colored_tag] for x in self.get_attributes('tags')]
            tag_to_num = {tag: num for num, tag in enumerate(set(tags))}
            plt_kwargs['c'] = np.array([tag_to_num[ni] for ni in tags])
            plt_kwargs['cmap'] = plt.get_cmap(colormap)

        plt.scatter(**plt_kwargs)

        if not show_axis:
            plt.gca().set_axis_off()
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())

        if output:
            plt.savefig(output, bbox_inches='tight', pad_inches=0.1)
        else:
            plt.show()
