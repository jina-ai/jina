__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any
from .. import BaseEvaluator


class BaseCraftingEvaluator(BaseEvaluator):
    """A :class:`BaseCraftingEvaluator` evaluates the difference between doc and groundtruth content
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def evaluate(self, doc_content: Any, groundtruth_content: Any, *args, **kwargs) -> float:
        """"
        :param doc_content: the content of the document
        :param groundtruth_content: the expected content of the document
        :return the evaluation metric value for the request document
        """
        raise NotImplementedError
