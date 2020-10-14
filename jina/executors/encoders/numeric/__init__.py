__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


from typing import Optional

import numpy as np
from jina.excepts import UndefinedModel
from jina.executors.decorators import batching
from .. import BaseNumericEncoder


class TransformEncoder(BaseNumericEncoder):
    """
    :class:`TransformEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`
    """

    def __init__(self,
                 output_dim: int = 64,
                 model_path: Optional[str] = None,
                 random_state: int = 2020,
                 *args,
                 **kwargs):
        """
        :param model_path: path from where to pickle the sklearn model.
        """
        super().__init__(*args, **kwargs)
        self.model_path = model_path
        self.output_dim = output_dim
        self.random_state = random_state

    def post_init(self) -> None:
        import pickle
        self.model = None
        if self.model_path:
            with open(self.model_path, 'rb') as model_file:
                self.model = pickle.load(model_file)

    @batching
    def train(self, data: 'np.ndarray', *args, **kwargs) -> None:
        if not self.model:
            raise UndefinedModel(
                'Model is not defined: Provide a loadable pickled model, or defined any specific TransformEncoder')
        num_samples, num_features = data.shape
        if not getattr(self, 'num_features', None):
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
