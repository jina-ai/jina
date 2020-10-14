from typing import Sequence, Any

from jina.executors.evaluators.rank import BaseRankingEvaluator
from jina.executors.evaluators.decorators import as_aggregator


class PrecisionEvaluator(BaseRankingEvaluator):
    """A :class:`PrecisionEvaluator` evaluates the Precision of the search.
       It computes how many of the first given `eval_at` matches are found in the groundtruth
    """

    def __init__(self, eval_at: int,  *args, **kwargs):
        """"
        :param eval_at: k at which evaluation is performed
        """
        super().__init__(*args, **kwargs)
        self.eval_at = eval_at

    @property
    def complete_name(self):
        return f'Precision@{self.eval_at}'

    @as_aggregator
    def evaluate(self, matches_ids: Sequence[Any], groundtruth_ids: Sequence[Any], *args, **kwargs) -> float:
        """"
        :param matches_ids: the matched document identifiers from the request as matched by jina indexers and rankers
        :param groundtruth_ids: the expected documents matches ids sorted as they are expected
        :return the evaluation metric value for the request document
        """
        ret = 0.0
        for doc_id in matches_ids[:self.eval_at]:
            if doc_id in groundtruth_ids:
                ret += 1.0

        divisor = min(self.eval_at, len(groundtruth_ids))
        if divisor == 0.0:
            """TODO: Agree on a behavior"""
            return 0.0
        else:
            return ret / divisor
