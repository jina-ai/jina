from typing import Sequence, Any, Optional

from ..rank import BaseRankingEvaluator


class PrecisionEvaluator(BaseRankingEvaluator):
    """A :class:`PrecisionEvaluator` evaluates the Precision of the search.
    It computes how many of the first given `eval_at` matches are found in the groundtruth
    """

    def __init__(self, eval_at: Optional[int] = None, *args, **kwargs):
        """ "
        :param eval_at: the point at which evaluation is computed, if None give, will consider all the input to evaluate
        """
        super().__init__(*args, **kwargs)
        self.eval_at = eval_at

    def evaluate(
        self, actual: Sequence[Any], desired: Sequence[Any], *args, **kwargs
    ) -> float:
        """ "
        :param actual: the matched document identifiers from the request as matched by jina indexers and rankers
        :param desired: the expected documents matches ids sorted as they are expected
        :return the evaluation metric value for the request document
        """
        if self.eval_at == 0:
            return 0.0
        actual_at_k = actual[: self.eval_at] if self.eval_at else actual
        ret = len(set(actual_at_k).intersection(set(desired)))
        sub = len(actual_at_k)
        return ret / sub if sub != 0 else 0.0
