__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from ..decorators import as_aggregator
from . import BaseTextEvaluator


class TextLengthEvaluator(BaseTextEvaluator):
    """A :class:`TextLengthEvaluator` evaluates the different lengths between doc and groundtruth text
    """

    @property
    def metric(self):
        return 'Length'

    @as_aggregator
    def evaluate(self, doc_content: str, groundtruth_content: str, *args, **kwargs) -> float:
        """"
        :param doc_content: the text of the document
        :param groundtruth_content: the expected text of the document
        :return the evaluation metric value for the request document
        """
        return abs(len(doc_content) - len(groundtruth_content))
