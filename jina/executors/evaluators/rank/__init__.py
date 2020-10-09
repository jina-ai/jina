__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Sequence, Any

from .. import BaseEvaluator


class BaseRankingEvaluator(BaseEvaluator):
    """A :class:`BaseRankingEvaluator` evaluates the content of matches against the expected GroundTruth.
    It is used to evaluate messages coming out from Indexers and Rankers and compares matches with groundtruths
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_init(self):
        super().post_init()
        self.num_documents = 0
        self.sum = 0

    @property
    def avg(self):
        if self.num_documents == 0:
            return 0.0
        return self.sum / self.num_documents

    @property
    def complete_name(self):
        return self.name

    def evaluate(self, matches_ids: Sequence[Any], groundtruth_ids: Sequence[Any], *args, **kwargs) -> float:
        """"
        :param matches_ids: the matched document identifiers from the request as matched by jina indexers and rankers
        :param groundtruth_ids: the expected documents matches ids sorted as they are expected
        :return the evaluation metric value for the request document
        """
        raise NotImplementedError
