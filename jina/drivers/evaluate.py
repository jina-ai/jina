__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from . import BaseExecutableDriver
from .helper import DocGroundtruthPair, pb2array
from jina.proto import jina_pb2


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

    @property
    def id(self):
        if self.pea:
            return self.pea.name
        else:
            return self.__class__.__name__

    def _apply_all(self, groundtruth_pairs: Iterable['DocGroundtruthPair'],
                   context_groundtruth_pair: 'DocGroundtruthPair',
                   *args,
                   **kwargs) -> None:
        pass


class RankingEvaluationDriver(BaseEvaluationDriver):
    """Drivers used to pass `matches` from documents and groundtruths to an executor and add the evaluation value
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


class EncodeEvaluationDriver(BaseEvaluationDriver):
    """Drivers used to pass `embedding` from documents and groundtruths to an executor and add the evaluation value
    """

    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

    def _apply_all(self,
                   groundtruth_pairs: Iterable[DocGroundtruthPair],
                   *args,
                   **kwargs) -> None:
        for doc_groundtruth in groundtruth_pairs:
            doc = doc_groundtruth.doc
            groundtruth = doc_groundtruth.groundtruth
            evaluation = doc.evaluations.add()
            evaluation.value = self.exec_fn(pb2array(doc.embedding), pb2array(groundtruth.embedding))
            evaluation.op_name = f'{self.id}-{self.exec.metric_name}'
            evaluation.ref_id = groundtruth.id


class CraftEvaluationDriver(BaseEvaluationDriver):
    """Drivers used to pass a content field from documents and groundtruths to an executor and add the evaluation value
    """

    def __init__(self,
                 field: str = 'text',
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.field = field

    def _apply_all(self,
                   groundtruth_pairs: Iterable[DocGroundtruthPair],
                   *args,
                   **kwargs) -> None:
        for doc_groundtruth in groundtruth_pairs:
            doc = doc_groundtruth.doc
            groundtruth = doc_groundtruth.groundtruth
            evaluation = doc.evaluations.add()

            doc_content = getattr(doc, self.field)
            gt_content = getattr(groundtruth, self.field)
            if isinstance(doc_content, jina_pb2.NdArray):
                doc_content = pb2array(doc_content)
            if isinstance(gt_content, jina_pb2.NdArray):
                gt_content = pb2array(gt_content)
            evaluation.value = self.exec_fn(doc_content, gt_content)
            evaluation.op_name = f'{self.id}-{self.exec.metric_name}'
            evaluation.ref_id = groundtruth.id