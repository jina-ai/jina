__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any

from .. import BaseEvaluator


class BaseTextEvaluator(BaseEvaluator):
    """A :class:`BaseTextEvaluator` evaluates the difference between doc and groundtruth text
    """

    def evaluate(self, prediction: Any, groundtruth: Any, *args, **kwargs) -> float:
        """"
        :param prediction: the content of the document
        :param groundtruth: the expected content of the document
        :return the evaluation metric value for the request document
        """
        raise NotImplementedError
