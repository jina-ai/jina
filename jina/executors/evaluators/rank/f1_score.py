from typing import Sequence, Any

from ..rank import BaseRankingEvaluator


class F1Evaluator(BaseRankingEvaluator):
    """A :class:`F1Evaluator` evaluates the f1 score of the search.
       It computes by applying the function: f1 = 2*(precision*recall)/(precision+recall)
    """

    @property
    def metric(self):
        return f'F1_score@{self.eval_at}'

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

        recall = ret/len(desired)
        divisor = min(self.eval_at, len(desired))
        
        if divisor != 0.0:
            precision = ret / divisor 
        else:
            precision = 0

        return 2*(precision*recall)/(precision+recall)
