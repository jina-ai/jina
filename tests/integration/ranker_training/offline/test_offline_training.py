import math
import pickle
from pathlib import Path

import pytest
import numpy as np

from jina.executors.rankers.trainer import RankerTrainer

'''
User -> Train request -> RankTrainer Train -> RankTrainer Dump Weights/Parameters -> To be loaded in Ranker
'''


class MockRankerTrainer(RankerTrainer):
    """pass"""

    WEIGHT_SCALE = 1 / max(1.0, (2 + 2) / 2.0)
    WEIGHT_LIMIT = math.sqrt(3.0 * WEIGHT_SCALE)
    WEIGHT_FILENAME = 'weights.txt'

    def __init__(self, params: dict = None, weights_shape: float = (2, 2)):
        super().__init__()
        self._params = params
        self._weights_shape = weights_shape
        self._weights = np.random.uniform(
            -self.WEIGHT_LIMIT, self.WEIGHT_LIMIT, size=weights_shape
        )

    def train(self, *args, **kwargs):
        # Mock the training process, generate a new random weight matrix.
        self._weights = np.random.uniform(
            -self.WEIGHT_LIMIT, self.WEIGHT_LIMIT, size=self._weights_shape
        )

    def save(self, path: str):
        """
        Save the weights of the ranker model.
        """
        path = Path(path)
        weights_path = path.joinpath(self.WEIGHT_FILENAME)

        if not path.exists():
            path.mkdir(parents=True)
        else:
            raise FileExistsError(f'{path} already exist, fail to save.')

        with open(weights_path, mode='wb') as weights_file:
            pickle.dump(self._weights, weights_file)

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, key, value):
        self.params[key] = value

    @property
    def weights(self):
        return self._weights
