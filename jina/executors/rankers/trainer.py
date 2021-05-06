__copyright__ = "Copyright (c) 2021 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from .. import BaseExecutor


class RankerTrainer(BaseExecutor):
    """pass"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def train(self, *args, **kwargs):
        """Train ranker based on user feedback, updating ranker weights based on
        the `loss` function."""
        raise NotImplementedError

    def save(self, filename: str):
        """
        Save the weights of the ranker model.
        """
        raise NotImplementedError
