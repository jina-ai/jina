__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable, Any, List

from . import BaseExecutableDriver
from .helper import DocGroundtruthPair, pb2array
from .search import KVSearchDriver
from ..proto import jina_pb2


class BaseEvaluateDriver(BaseExecutableDriver):
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
    def metric(self):
        if self.pea:
            return self.pea.name
        else:
            return self.__class__.__name__

    def _apply_all(
            self,
            docs: Iterable['jina_pb2.Document'],
            context_doc: 'jina_pb2.Document' = None,
            field: str = None,
            *args,
            **kwargs
    ) -> None:
        for doc_groundtruth in docs:
            doc = doc_groundtruth.doc
            groundtruth = doc_groundtruth.groundtruth
            evaluation = doc.evaluations.add()
            evaluation.value = self.exec_fn(self.extract(doc), self.extract(groundtruth))
            evaluation.op_name = f'{self.metric}-{self.exec.metric}'
            evaluation.ref_id = groundtruth.id

    def extract(self, doc: 'jina_pb2.Document') -> Any:
        """Extracting the to-be-evaluated field from the document.
        Drivers inherit from :class:`BaseEvaluateDriver` must implement this method.

        This function will be invoked two times in :meth:`_apply_all`:
        once with actual doc, once with groundtruth doc.
        """
        raise NotImplementedError


class RankEvaluateDriver(BaseEvaluateDriver):
    """Drivers used to pass `matches` from documents and groundtruths to an executor and add the evaluation value
    """

    def __init__(self,
                 id_tag: str = 'id',
                 *args,
                 **kwargs):
        """

        :param id_tag: the name of the tag to be extracted, when not given then ``document.id`` is used.
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.id_tag = id_tag

    def extract(self, doc: 'jina_pb2.Document') -> List[int]:
        if self.id_tag:
            return [x.tags[self.id_tag] for x in doc.matches]
        else:
            return [x.id for x in doc.matches]


class EmbeddingEvaluateDriver(BaseEvaluateDriver):
    """Drivers used to pass `embedding` from documents and groundtruths to an executor and add the evaluation value
    """

    def extract(self, doc: 'jina_pb2.Document'):
        return pb2array(doc.embedding)


class TextEvaluateDriver(BaseEvaluateDriver):
    """Drivers used to pass a content field from documents and groundtruths to an executor and add the evaluation value
    """

    def extract(self, doc: 'jina_pb2.Document'):
        return doc.text


class LoadGroundTruthDriver(KVSearchDriver):
    """Driver used to search for the `document key` in a KVIndex to find the corresponding groundtruth.
     (This driver does not use the `recursive structure` of jina Documents, and will not consider the `traversal_path` argument.
     It only retrieves `groundtruth` taking documents at root as key)
     This driver's job is to fill the `request` groundtruth with the corresponding groundtruth for each document if found in the corresponding KVIndexer.

    .. warning::
        The documents that are not found to have an indexed groundtruth are removed from the `request` so that the `Evaluator` only
        works with documents which have groundtruth.
    """

    def __call__(self, *args, **kwargs):
        assert len(self.req.groundtruths) == 0
        miss_idx = []  #: missed hit results, some documents may not have groundtruth and thus will be removed
        for idx, doc in enumerate(self.req.docs):
            serialized_groundtruth = self.exec_fn(self.id2hash(doc.id))
            if serialized_groundtruth:
                gt = self.req.groundtruths.add()
                gt.ParseFromString(serialized_groundtruth)
            else:
                miss_idx.append(idx)
        # delete non-existed matches in reverse
        for j in reversed(miss_idx):
            del self.req.docs[j]
