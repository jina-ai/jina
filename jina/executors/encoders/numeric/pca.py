__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from .. import BaseNumericEncoder
from ...decorators import batching, require_train


class IncrementalPCAEncoder(BaseNumericEncoder):
    """
    :class:`IncrementalPCAEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`.

    .. note::
        :class:`IncrementalPCAEncoder` must be trained before calling ``encode()``. This encoder can be trained in an
        incremental way.
    """

    def __init__(self,
                 output_dim: int,
                 num_features: int = None,
                 whiten: bool = False,
                 *args,
                 **kwargs):
        """

        :param output_dim: the output size.
        :param num_features: the number of input features.  If ``num_features`` is None, then ``num_features`` is
            inferred from the data
        :param whiten: If whiten is false, the data is already considered to be whitened, and no whitening is performed.
        """
        super().__init__(*args, **kwargs)
        self.output_dim = output_dim
        self.whiten = whiten
        self.num_features = num_features
        self.is_trained = False
        self.model = None

    def post_init(self):
        from sklearn.decomposition import IncrementalPCA
        if not self.model:
            self.model = IncrementalPCA(
                n_components=self.output_dim,
                whiten=self.whiten)

    @batching
    def train(self, data: 'np.ndarray', *args, **kwargs):
        num_samples, num_features = data.shape
        if not self.num_features:
            self.num_features = num_features
        if num_samples < 5 * num_features:
            self.logger.warning(
                'the batch size (={}) is suggested to be 5 * num_features(={}) to provide a balance between '
                'approximation accuracy and memory consumption.'.format(num_samples, num_features))
        self.model.partial_fit(data)
        self.is_trained = True

    @require_train
    @batching
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """
        :param data: a `B x T` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``
        """
        _, num_features = data.shape
        return self.model.transform(data)
