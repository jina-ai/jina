__copyright__ = "Copyright (c) 2021 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from .. import BaseExecutor


class RankerTrainer(BaseExecutor):
    """Class :class:`RankerTrainer` is used to train a ranker for ranker fine-tunning purpose.
    such as offline-learning and online-learning.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def train(self, *args, **kwargs):
        """Train ranker based on user feedback, updating ranker weights based on
        the `loss` function.

        :param args: Additional arguments.
        :param kwargs: Additional key value arguments.
        """
        raise NotImplementedError

    def save(self):
        """Save the of the ranker model."""
        raise NotImplementedError
