__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import BaseTextEvaluator


class TextLengthEvaluator(BaseTextEvaluator):
    """A :class:`TextLengthEvaluator` evaluates the different lengths between actual and desired text
    """

    @property
    def metric(self):
        return 'Length'

    def evaluate(self, actual: str, desired: str, *args, **kwargs) -> float:
        """"
        :param actual: the text of the document
        :param desired: the expected text of the document
        :return the evaluation metric value for the request document
        """
        return abs(len(actual) - len(desired))
