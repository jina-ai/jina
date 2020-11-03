from typing import Sequence, Any
from ..rank import BaseRankingEvaluator
import numpy as np


class AveragePrecisionEvaluator(BaseRankingEvaluator):
    """A :class:`AveragePrecisionEvaluator` evaluates the Average Precision of the search.
       https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval)#Average_precision
    """

    @property
    def metric(self):
        return 'AveragePrecision'

    def evaluate(self, actual: Sequence[Any], desired: Sequence[Any], *args, **kwargs) -> float:
        """"
        :param actual: the matched document identifiers from the request as matched by jina indexers and rankers
        :param desired: the expected documents matches ids sorted as they are expected
        :return the evaluation metric value for the request document
        """
        matches = []
        for idx, doc_id in enumerate(desired):
            matches.append(doc_id in actual[:idx+1])
        matches = np.array(matches)
        cumsum = np.cumsum(matches)
        precision = cumsum / np.arange(1, len(matches) + 1)

        # Does not match behaviour in
        # https://github.com/jina-ai/jina/blob/master/tests/unit/executors/evaluators/rank/test_precision.py#L10
        precision = np.insert(precision, 0, 1.)

        recall = cumsum / len(matches)
        # copy behaviour as in
        # https://github.com/jina-ai/jina/blob/master/tests/unit/executors/evaluators/rank/test_recall.py#L10
        recall = np.insert(recall, 0, 0.)

        ap = np.sum(np.diff(recall) * ((precision[1:] + precision[:-1]) / 2))
        return ap
