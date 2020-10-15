__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from . import BaseExecutableDriver
from .helper import DocGroundtruthPair


class BaseEvaluationDriver(BaseExecutableDriver):
    def __init__(self, executor: str = None,
                 method: str = 'evaluate',
                 *args,
                 **kwargs):
        super().__init__(executor, method, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        assert len(self.req.docs) == len(self.req.groundtruths)
        docs_groundtruths = [DocGroundtruthPair(doc, groundtruth) for doc, groundtruth in
                             zip(self.req.docs, self.req.groundtruths)]
        self._traverse_apply(docs_groundtruths, *args, **kwargs)

    def _apply_all(self, groundtruth_pairs: Iterable['DocGroundtruthPair'],
                   context_groundtruth_pair: 'DocGroundtruthPair',
                   *args,
                   **kwargs) -> None:
        pass


class RankingEvaluationDriver(BaseEvaluationDriver):
    """Drivers inherited from this Driver will bind :meth:`evaluate` by default
    """

    def __init__(self,
                 id_tag: str = 'id',
                 *args,
                 **kwargs):
        """

        :param id_tag: the name of the tag to be extracted
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.id_tag = id_tag

    @property
    def id(self):
        if self.pea:
            return self.pea.name
        else:
            return self.__class__.__name__

    def _apply_all(self,
                   groundtruth_pairs: Iterable[DocGroundtruthPair],
                   *args,
                   **kwargs) -> None:
        for doc_groundtruth in groundtruth_pairs:
            doc = doc_groundtruth.doc
            groundtruth = doc_groundtruth.groundtruth

            evaluation = doc.evaluations.add()
            matches_ids = [x.tags[self.id_tag] for x in doc.matches]
            groundtruth_ids = [x.tags[self.id_tag] for x in groundtruth.matches]
            evaluation.value = self.exec_fn(matches_ids, groundtruth_ids)
            evaluation.op_name = f'{self.id}-{self.exec.metric_name}'
            evaluation.ref_id = groundtruth.id
