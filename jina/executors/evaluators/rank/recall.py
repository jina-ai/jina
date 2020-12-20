from typing import Sequence, Any

from . import BaseRankingEvaluator


class RecallEvaluator(BaseRankingEvaluator):
    """A :class:`RecallEvaluator` evaluates the Precision of the search.
       It computes how many of the first given `eval_at` groundtruth are found in the matches
    """

    metric = 'Recall@N'

    def evaluate(self, actual: Sequence[Any], desired: Sequence[Any], *args, **kwargs) -> float:
        """"
        :param actual: the matched document identifiers from the request as matched by jina indexers and rankers
        :param desired: the expected documents matches ids sorted as they are expected
        :return the evaluation metric value for the request document
        """
        ret = len(set(actual).intersection(set(desired)))
        return ret / len(desired)
