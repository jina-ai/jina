__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import FitTransformEncoder


class TSNEEncoder(FitTransformEncoder):
    """
    :class:`TSNEEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`.
    https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html
    """

    def __init__(self, output_dim: int, random_state=2020, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dim = output_dim
        self.random_state = random_state

    def post_init(self):
        super().post_init()
        if not self.model:
            from sklearn.manifold import TSNE
            self.model = TSNE(n_components=self.output_dim, random_state=self.random_state)
