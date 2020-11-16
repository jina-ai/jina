__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Sequence, Any

from . import BaseExecutableDriver
from .helper import DocGroundtruthPair
from .querylang.queryset.dunderkey import dunder_get
from .search import KVSearchDriver
from ..proto import jina_pb2
from jina.types.ndarray.generic import NdArray


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
            docs: Sequence['jina_pb2.DocumentProto'],
            context_doc: 'jina_pb2.DocumentProto' = None,
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

    def extract(self, doc: 'jina_pb2.DocumentProto') -> Any:
        """Extracting the to-be-evaluated field from the document.
        Drivers inherit from :class:`BaseEvaluateDriver` must implement this method.

        This function will be invoked two times in :meth:`_apply_all`:
        once with actual doc, once with groundtruth doc.
        """
        raise NotImplementedError


class FieldEvaluateDriver(BaseEvaluateDriver):
    """
    Evaluate on the values from certain field, the extraction is implemented with :meth:`dunder_get`
    """

    def __init__(self, field: str,
                 *args,
                 **kwargs):
        """

        :param field: the field name to be extracted from the Protobuf
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.field = field

    def extract(self, doc: 'jina_pb2.DocumentProto') -> Any:
        r = dunder_get(doc, self.field)
        if isinstance(r, jina_pb2.NdArrayProto):
            r = NdArray(r).value
        return r


class RankEvaluateDriver(FieldEvaluateDriver):
    """Drivers used to pass `matches` from documents and groundtruths to an executor and add the evaluation value

        - Example fields:
        ['tags__id', 'id', 'score__value]
    """

    def __init__(self,
                 field: str = 'tags__id',
                 *args,
                 **kwargs):
        """
        :param args:
        :param kwargs:
        """
        super().__init__(field, *args, **kwargs)

    def extract(self, doc: 'jina_pb2.DocumentProto'):
        return [dunder_get(x, self.field) for x in doc.matches]


class NDArrayEvaluateDriver(FieldEvaluateDriver):
    """Drivers used to pass `embedding` from documents and groundtruths to an executor and add the evaluation value

    - Valid fields:
        ['blob', 'embedding']

    """

    def __init__(self, field: str = 'embedding', *args, **kwargs):
        super().__init__(field, *args, **kwargs)


class TextEvaluateDriver(FieldEvaluateDriver):
    """Drivers used to pass a content field from documents and groundtruths to an executor and add the evaluation value

    - Valid fields:
                ['id',
                 'level_name',
                 'parent_id',
                 'text',
                 'mime_type',
                 'uri',
                 'modality']
    """

    def __init__(self, field: str = 'text', *args, **kwargs):
        super().__init__(field, *args, **kwargs)


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
