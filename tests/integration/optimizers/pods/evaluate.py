from typing import Sequence, Any

from jina.executors.evaluators.rank import BaseRankingEvaluator


class MyEvaluator(BaseRankingEvaluator):
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
        desired_label = desired[0]

        ret = 0.0
        for match_label in actual[:self.eval_at]:
            if match_label == desired_label:
                ret += 1.0

        divisor = min(self.eval_at, len(actual))
        return ret / divisor if divisor != 0.0 else 0.0
