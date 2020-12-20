from typing import Sequence, Any

from ..rank import BaseRankingEvaluator


class PrecisionEvaluator(BaseRankingEvaluator):
    """A :class:`PrecisionEvaluator` evaluates the Precision of the search.
       It computes how many of the first given `eval_at` matches are found in the groundtruth
    """

    metric = 'Precision@N'

    def evaluate(self, actual: Sequence[Any], desired: Sequence[Any], *args, **kwargs) -> float:
        """"
        :param actual: the matched document identifiers from the request as matched by jina indexers and rankers
        :param desired: the expected documents matches ids sorted as they are expected
        :return the evaluation metric value for the request document
        """
        ret = len(set(actual).intersection(set(desired)))
        sub = len(actual)
        return ret / sub if sub !=0 else 0.
