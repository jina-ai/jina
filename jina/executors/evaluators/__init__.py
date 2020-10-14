__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any

from .. import BaseExecutor


class BaseEvaluator(BaseExecutor):
    """A :class:`BaseEvaluator` is used to evaluate different messages coming from any kind of executor
    """

    @property
    def metric_name(self):
        """Get the name of the evaluation metric """
        return self.name

    def evaluate(self, prediction: Any, groundtruth: Any, *args, **kwargs) -> float:
        raise NotImplementedError
