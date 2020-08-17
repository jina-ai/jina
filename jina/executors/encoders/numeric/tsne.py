__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import FitTransformEncoder


class TSNEEncoder(FitTransformEncoder):
    """
    :class:`TSNEEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`.
    https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_init(self):
        super().post_init()
        if not self.model:
            from sklearn.manifold import TSNE
            self.model = TSNE(n_components=self.output_dim, random_state=self.random_state)
