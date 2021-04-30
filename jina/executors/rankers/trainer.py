__copyright__ = "Copyright (c) 2021 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


from .. import BaseExecutor


class RankerTrainer(BaseExecutor):
    """pass"""

    def __init__(self, params: dict = None):
        super().__init__()
        self._params = params

    def train(self):
        """Train ranker based on user feedback, updating ranker weights based on
        the `loss` function."""
        raise NotImplementedError

    def save(self, ranker_path: str):
        """
        Save the ranker model.
        """
        raise NotImplementedError

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
