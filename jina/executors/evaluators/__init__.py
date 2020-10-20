__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any

from .. import BaseExecutor


class BaseEvaluator(BaseExecutor):
    """A :class:`BaseEvaluator` is used to evaluate different messages coming from any kind of executor
    """

    def post_init(self):
        super().post_init()
        self._num_docs = 0
        self._total_sum = 0

    @property
    def avg(self):
        if self._num_docs == 0:
            return 0.0
        return self._total_sum / self._num_docs

    @property
    def metric(self) -> str:
        """Get the name of the evaluation metric """
        raise NotImplementedError

    def evaluate(self, prediction: Any, groundtruth: Any, *args, **kwargs) -> float:
        raise NotImplementedError
