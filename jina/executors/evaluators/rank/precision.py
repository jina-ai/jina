from typing import Sequence, Any

from ..rank import BaseRankingEvaluator


class PrecisionEvaluator(BaseRankingEvaluator):
    """A :class:`PrecisionEvaluator` evaluates the Precision of the search.
       It computes how many of the first given `eval_at` matches are found in the groundtruth
    """

    @property
    def metric(self):
        return f'Precision@{self.eval_at}'

    def evaluate(self, actual: Sequence[Any], desired: Sequence[Any], *args, **kwargs) -> float:
        """"
        :param actual: the matched document identifiers from the request as matched by jina indexers and rankers
        :param desired: the expected documents matches ids sorted as they are expected
        :return the evaluation metric value for the request document
        """
        ret = len(set(actual[:self.eval_at]).intersection(set(desired)))
        divisor = min(self.eval_at, len(desired))
        return ret / divisor if divisor != 0.0 else 0.0
