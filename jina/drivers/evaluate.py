__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any, Iterator

import numpy

from . import BaseExecutableDriver
from .querylang.queryset.dunderkey import dunder_get
from .search import KVSearchDriver
from ..types.document import Document
from ..types.document.helper import DocGroundtruthPair


class BaseEvaluateDriver(BaseExecutableDriver):
    def __init__(self, executor: str = None,
                 method: str = 'evaluate',
                 running_avg: bool = False,
                 *args,
                 **kwargs):
        """
        :param executor: the name of the sub-executor, only necessary when :class:`jina.executors.compound.CompoundExecutor` is used
        :param method: the function name of the executor that the driver feeds to
        :param running_avg: always return running average instead of value of the current run
        :param args:
        :param kwargs:

        .. warning::

            When ``running_avg=True``, then the running mean is returned. So far at Jina 0.8.10,
             there is no way to reset the running statistics. If you have a query Flow running multiple queries,
             you may want to make sure the running statistics is meaningful across multiple runs.
        """
        super().__init__(executor, method, *args, **kwargs)
        self._running_avg = running_avg

    def __call__(self, *args, **kwargs):
        docs_groundtruths = [DocGroundtruthPair(doc, groundtruth) for doc, groundtruth in
                             zip(self.docs, self.req.groundtruths)]
        self._traverse_apply(docs_groundtruths, *args, **kwargs)

    def _apply_all(
            self,
            docs: Iterator['DocGroundtruthPair'],
            *args,
            **kwargs
    ) -> None:
        for doc_groundtruth in docs:
            doc = doc_groundtruth.doc
            groundtruth = doc_groundtruth.groundtruth
            evaluation = doc.evaluations.add()
            evaluation.value = self.exec_fn(self.extract(doc), self.extract(groundtruth))
            if self._running_avg:
                evaluation.value = self.exec.mean

            if getattr(self.exec, 'eval_at', None):
                evaluation.op_name = f'{self.exec.__class__.__name__}@{self.exec.eval_at}'
            else:
                evaluation.op_name = self.exec.__class__.__name__
            evaluation.ref_id = groundtruth.id

    def extract(self, doc: 'Document') -> Any:
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

    def extract(self, doc: 'Document') -> Any:
        return dunder_get(doc, self.field)


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

    def extract(self, doc: 'Document'):
        r = [dunder_get(x, self.field) for x in doc.matches]
        # flatten nested list but useless depth, e.g. [[1,2,3,4]]
        return list(numpy.array(r).flat)


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
        miss_idx = []  #: missed hit results, some documents may not have groundtruth and thus will be removed
        for idx, doc in enumerate(self.docs):
            serialized_groundtruth = self.exec_fn(int(doc.id))
            if serialized_groundtruth:
                self.req.groundtruths.append(Document(serialized_groundtruth))
            else:
                miss_idx.append(idx)
        # delete non-existed matches in reverse
        for j in reversed(miss_idx):
            del self.docs[j]
