import numpy as np

from typing import Optional
from .. import BaseNumericEncoder
from ...decorators import batching
from jina.excepts import UndefinedModel


class FitTransformEncoder(BaseNumericEncoder):
    """
    :class:`FitTransformEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`
    Parent class for RandomGaussianEncoder, RandomSparseEncoder and TSNEEncoder to prevent redundant code
    """

    def __init__(self, model_path: Optional[str],
                 *args,
                 **kwargs):
        """
        :param output_dim: the output size.
        """
        super().__init__(*args, **kwargs)
        self.model_path = model_path

    def post_init(self):
        import pickle
        self.model = None
        if self.model_path:
            with open(self.model_path, 'rb') as model_file:
                self.model = pickle.load(model_file)

    @batching
    def train(self, data: 'np.ndarray', *args, **kwargs):
        if not self.model:
            raise UndefinedModel(
                'Model is not defined: Provide a loadable pickled model, or defined any specific FitTransformEncoder')
        num_samples, num_features = data.shape
        if not self.num_features:
            self.num_features = num_features
        if num_samples < 5 * num_features:
            self.logger.warning(
                'the batch size (={}) is suggested to be 5 * num_features(={}) to provide a balance between '
                'approximation accuracy and memory consumption.'.format(num_samples, num_features))
        self.model.fit(data)
        self.is_trained = True

    @batching
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """
        :param data: a `B x T` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``
        """
        return self.model.transform(data)
