from typing import Sequence, Any

from . import BaseRankingEvaluator


class RecallEvaluator(BaseRankingEvaluator):
    """A :class:`RecallEvaluator` evaluates the Precision of the search.
       It computes how many of the first given `eval_at` groundtruth are found in the matches
    """

    @property
    def metric(self):
        return f'Recall@{self.eval_at}'

    def evaluate(self, actual: Sequence[Any], desired: Sequence[Any], *args, **kwargs) -> float:
        """"
        :param actual: the matched document identifiers from the request as matched by jina indexers and rankers
        :param desired: the expected documents matches ids sorted as they are expected
        :return the evaluation metric value for the request document
        """
        if not desired:
            """TODO: Agree on a behavior"""
            return 0.0

        ret = 0.0
        for doc_id in actual[:self.eval_at]:
            if doc_id in desired:
                ret += 1.0

        return ret / len(desired)
