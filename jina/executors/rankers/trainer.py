__copyright__ = "Copyright (c) 2021 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import math

import numpy as np

from .. import BaseExecutor


class RankerTrainer(BaseExecutor):
    """pass"""

    WEIGHT_SCALE = 1 / max(1.0, (2 + 2) / 2.0)
    WEIGHT_LIMIT = math.sqrt(3.0 * WEIGHT_SCALE)

    def __init__(self, params: dict = None, weights_shape: float = (2, 2)):
        super().__init__()
        self._params = params
        self._weights = np.random.uniform(
            -self.WEIGHT_LIMIT, self.WEIGHT_LIMIT, size=weights_shape
        )

    def train(self):
        """Train ranker based on user feedback, updating ranker weights based on
        the `loss` function."""
        raise NotImplementedError

    def save_weights(self, path: str):
        """
        Save the weights of the ranker model.
        """
        raise NotImplementedError

    def load_weights(self, path: str):
        """
        Load the weights of the ranker model.
        """
        raise NotImplementedError

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, key, value):
        self.params[key] = value

    @property
    def weights(self):
        return self._weights
