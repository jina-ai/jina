__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any

from .. import BaseEvaluator
from jina.drivers.evaluate import TextEvaluateDriver


class BaseTextEvaluator(BaseEvaluator):
    """A :class:`BaseTextEvaluator` evaluates the difference between actual and desired text
    """

    test_drivers = (TextEvaluateDriver, )

    def evaluate(self, actual: Any, desired: Any, *args, **kwargs) -> float:
        """"
        :param actual: the content of the document
        :param desired: the expected content of the document
        :return the evaluation metric value for the request document
        """
        raise NotImplementedError
