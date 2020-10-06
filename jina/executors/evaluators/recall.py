from typing import Sequence
from jina.proto import jina_pb2

from ..evaluators import BaseEvaluator


class RecallEvaluator(BaseEvaluator):
    """A :class:`RecallEvaluator` evaluates the Precision of the search.
       It computes how many of the first given `eval_at` groundtruth are found in the matches
    """

    def __init__(self, eval_at,  *args, **kwargs):
        """"
        :param eval_at: k at which evaluation is performed
        """
        super().__init__(*args, **kwargs)
        self.eval_at = eval_at

    def evaluate(self, matches: Sequence[jina_pb2.Document],
                 groundtruth: Sequence[jina_pb2.Document], *args, **kwargs) -> float:
        """"
        :param matches: the matched documents from the request as matched by jina indexers and rankers
        :param groundtruth: the expected documents matches sorted as they are expected
        :return the evaluation metric value for the request document
        """
        ret = 0.0
        matches_ids = map(lambda x: x.tags[self.id_tag], matches)
        groundtruth_ids = map(lambda x: x.tags[self.id_tag], groundtruth)
        for doc_id in groundtruth_ids[:, self.eval_at]:
            if doc_id in matches_ids:
                ret += 1.0

        min = min(self.eval_at, len(matches))
        return ret/min
