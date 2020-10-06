from typing import Sequence
from jina.proto import jina_pb2

from ..evaluators import BaseEvaluator


class PrecisionEvaluator(BaseEvaluator):
    """A :class:`PrecisionEvaluator` evaluates the Precision of the search.
       It computes how many of the first given `eval_at` matches are found in the groundtruth
    """

    def __init__(self, eval_at: int,  *args, **kwargs):
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
        matches_ids = list(map(lambda x: x.tags[self.id_tag], matches[:self.eval_at]))
        groundtruth_ids = list(map(lambda x: x.tags[self.id_tag], groundtruth))
        for doc_id in matches_ids:
            if doc_id in groundtruth_ids:
                ret += 1.0

        divisor = min(self.eval_at, len(groundtruth))
        if divisor == 0.0:
            """TODO: Agree on a behavior"""
            return 0.0
        else:
            return ret / divisor
