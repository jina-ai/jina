__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Sequence, Any

from .. import BaseEvaluator


class BaseRankingEvaluator(BaseEvaluator):
    """A :class:`BaseRankingEvaluator` evaluates the content of matches against the expected GroundTruth.
    It is used to evaluate messages coming out from Indexers and Rankers and compares matches with groundtruths
    """

    def evaluate(self, actual: Sequence[Any], desired: Sequence[Any], *args, **kwargs) -> float:
        """"
        :param actual: the matched document identifiers from the request as matched by jina indexers and rankers
        :param desired: the expected documents matches ids sorted as they are expected
        :return the evaluation metric value for the request document
        """
        raise NotImplementedError
