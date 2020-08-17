__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import FitTransformEncoder


class RandomGaussianEncoder(FitTransformEncoder):
    """
    :class:`RandomGaussianEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`
    https://scikit-learn.org/stable/modules/generated/sklearn.random_projection.GaussianRandomProjection.html
    """

    def __init__(self, output_dim: int, random_state=2020, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dim = output_dim
        self.random_state = random_state

    def post_init(self):
        super().post_init()
        if not self.model:
            from sklearn.random_projection import GaussianRandomProjection
            self.model = GaussianRandomProjection(n_components=self.output_dim, random_state=self.random_state)
