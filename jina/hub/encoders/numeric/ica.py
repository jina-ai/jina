__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import TransformEncoder


class FastICAEncoder(TransformEncoder):
    """
    :class:`FastICAEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`.

    .. note:: 
        :class:`FastICAEncoder` must be trained before calling ``encode()``.
    """

    def __init__(self, num_features: int = None, whiten: bool = False,
                 max_iter: int = 200, *args, **kwargs):
        """

        :param output_dim: the output size.
        :param num_features: the number of input features.  If ``num_features`` is None, then ``num_features`` is
            inferred from the data
        :param whiten: If whiten is false, the data is already considered to be whitened, and no whitening is performed.
        """
        super().__init__(*args, **kwargs)
        self.whiten = whiten
        self.num_features = num_features
        self.is_trained = False
        self.max_iter = max_iter
        self.model = None

    def post_init(self):
        super().post_init()
        if not self.model:
            from sklearn.decomposition import FastICA
            self.model = FastICA(
                n_components=self.output_dim,
                whiten=self.whiten,
                max_iter=self.max_iter)
