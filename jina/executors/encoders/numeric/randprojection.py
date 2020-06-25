__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from .. import BaseNumericEncoder
from ...decorators import batching


class RandomGaussianEncoder(BaseNumericEncoder):
    """
    :class:`RandomGaussianEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`
    https://scikit-learn.org/stable/modules/generated/sklearn.random_projection.GaussianRandomProjection.html
    """

    def __init__(self,
                 output_dim: int,
                 *args,
                 **kwargs):
        """
        :param output_dim: the output size.
        """
        super().__init__(*args, **kwargs)
        self.output_dim = output_dim
        self.model = None

    def post_init(self):
        from sklearn.random_projection import GaussianRandomProjection
        self.model = GaussianRandomProjection(n_components=self.output_dim)

    @batching
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """
        :param data: a `B x T` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``
        """
        return self.model.fit_transform(data)


class RandomSparseEncoder(BaseNumericEncoder):
    """
    :class:`RandomSparseEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`
    https://scikit-learn.org/stable/modules/generated/sklearn.random_projection.SparseRandomProjection.html
    """

    def __init__(self,
                 output_dim: int,
                 *args,
                 **kwargs):
        """
        :param output_dim: the output size.
        """
        super().__init__(*args, **kwargs)
        self.output_dim = output_dim
        self.model = None

    def post_init(self):
        from sklearn.random_projection import SparseRandomProjection
        self.model = SparseRandomProjection(n_components=self.output_dim)

    @batching
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """
        :param data: a `B x T` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``
        """
        return self.model.fit_transform(data)
