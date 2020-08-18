__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import TransformEncoder


class FeatureAgglomerationEncoder(TransformEncoder):
    """
    :class:`FeatureAgglomerationEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`
    https://scikit-learn.org/stable/modules/generated/sklearn.cluster.FeatureAgglomeration.html
    """

    def post_init(self):
        super().post_init()
        if not self.model:
            from sklearn.cluster import FeatureAgglomeration
            self.model = FeatureAgglomeration(n_clusters=self.output_dim)
