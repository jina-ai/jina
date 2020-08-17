__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import TransformEncoder


class RandomSparseEncoder(TransformEncoder):
    """
    :class:`RandomSparseEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`
    https://scikit-learn.org/stable/modules/generated/sklearn.random_projection.SparseRandomProjection.html
    """

    def post_init(self):
        super().post_init()
        if not self.model:
            from sklearn.random_projection import SparseRandomProjection
            self.model = SparseRandomProjection(n_components=self.output_dim, random_state=self.random_state)
