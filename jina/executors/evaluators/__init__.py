__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from math import sqrt
from typing import Any

from .running_stats import RunningStats
from .. import BaseExecutor


class BaseEvaluator(BaseExecutor):
    """A :class:`BaseEvaluator` is used to evaluate different messages coming from any kind of executor
    """

    def post_init(self):
        super().post_init()
        self._running_stats = RunningStats()

    @property
    def metric(self) -> str:
        """Get the name of the evaluation metric """
        raise NotImplementedError

    def evaluate(self, actual: Any, desired: Any, *args, **kwargs) -> float:
        raise NotImplementedError

    @property
    def mean(self) -> float:
        return self._running_stats.mean

    @property
    def std(self) -> float:
        return self._running_stats.std

    @property
    def variance(self) -> float:
        return self._running_stats.variance
