__copyright__ = "Copyright (c) 2021 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import abc

from . import BaseRanker


class RankerTrainer(abc.ABC):
    """pass"""

    def __init__(self, ranker: BaseRanker, params: dict = None):
        super().__init__()
        if not ranker.trainable:
            # TODO customize exception.
            raise Exception('The ranker is not trainable.')
        self._ranker = ranker
        self._params = params

    @abc.abstractmethod
    def train(self):
        """Train ranker based on user feedback, updating ranker weights based on
        the `loss` function."""
        pass

    @property
    def ranker(self) -> BaseRanker:
        return self._ranker

    @abc.abstractmethod
    def save(self, ranker_path: str):
        """
        Save the ranker model.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def load(self, ranker_path: str):
        """
        Load the ranker model.
        """
        raise NotImplementedError

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, key, value):
        self.params[key] = value
