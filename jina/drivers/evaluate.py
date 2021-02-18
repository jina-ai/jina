__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any, Iterator, Optional, Tuple, Union

import numpy as np

from . import BaseExecutableDriver, RecursiveMixin
from ..types.querylang.queryset.dunderkey import dunder_get
from .search import KVSearchDriver
from ..types.document import Document
from ..types.document.helper import DocGroundtruthPair
from ..helper import deprecated_alias


class BaseEvaluateDriver(RecursiveMixin, BaseExecutableDriver):
    """The Base Driver for evaluation operations.

    .. warning::

        When ``running_avg=True``, then the running mean is returned. So far at Jina 0.8.10,
         there is no way to reset the running statistics. If you have a query Flow running multiple queries,
         you may want to make sure the running statistics is meaningful across multiple runs.

    :param executor: the name of the sub-executor, only necessary when :class:`jina.executors.compound.CompoundExecutor` is used
    :param method: the function name of the executor that the driver feeds to
    :param running_avg: always return running average instead of value of the current run
    :param *args:
    :param **kwargs:
    """

    def __init__(self, executor: Optional[str] = None,
                 method: str = 'evaluate',
                 running_avg: bool = False,
                 *args,
                 **kwargs):
        super().__init__(executor, method, *args, **kwargs)
        self._running_avg = running_avg

    def __call__(self, *args, **kwargs):
        """Load the ground truth pairs

        :param *args: *args for _traverse_apply
        :param **kwargs: **kwargs for _traverse_apply
        """
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


        .. # noqa: DAR401
        :param doc: the Document
        """
        raise NotImplementedError


class FieldEvaluateDriver(BaseEvaluateDriver):
    """
    Evaluate on the values from certain field, the extraction is implemented with :meth:`dunder_get`
    """

    def __init__(self,
                 field: str,
                 *args,
                 **kwargs):
        """

        :param field: the field name to be extracted from the Protobuf
        :param *args: *args for super
        :param **kwargs: **kwargs for super
        """
        super().__init__(*args, **kwargs)
        self.field = field

    def extract(self, doc: 'Document') -> Any:
        """Extract the field from the Document

        :param doc: the Document
        :return: the data in the field
        """
        return dunder_get(doc, self.field)


class RankEvaluateDriver(BaseEvaluateDriver):
    """Drivers used to pass `matches` from documents and groundtruths to an executor and add the evaluation value

        - Example fields:
            ['tags__id', 'score__value]

    :param fields: the fields names to be extracted from the Protobuf.
            The differences with `:class:FieldEvaluateDriver` are:
                - More than one field is allowed. For instance, for NDCGComputation you may need to have both `ID` and `Relevance` information.
                - The fields are extracted from the `matches` of the `Documents` and the `Groundtruth` so it returns a sequence of values.
    :param *args:
    :param **kwargs:
    """

    @deprecated_alias(field=('fields', 0))
    def __init__(self,
                 fields: Union[str, Tuple[str]] = ('tags__id',),  # str mantained for backwards compatibility
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = fields

    @property
    def single_field(self):
        if isinstance(self.fields, str):
            return self.fields
        elif len(self.fields) == 1:
            return self.fields[0]

    def extract(self, doc: 'Document'):
        single_field = self.single_field
        if single_field:
            r = [dunder_get(x, single_field) for x in doc.matches]
            # TODO: Clean this, optimization for `hello-world` because it passes a list of 6k elements in a single
            #  match. See `pseudo_match` in helloworld/helper.py _get_groundtruths
            ret = list(np.array(r).flat)
        else:
            ret = [tuple(dunder_get(x, field) for field in self.fields) for x in doc.matches]

        return ret


class NDArrayEvaluateDriver(FieldEvaluateDriver):
    """Drivers used to pass `embedding` from documents and groundtruths to an executor and add the evaluation value

    .. note::
        - Valid fields:
                     ['blob', 'embedding']

    """

    def __init__(self, field: str = 'embedding', *args, **kwargs):
        super().__init__(field, *args, **kwargs)


class TextEvaluateDriver(FieldEvaluateDriver):
    """Drivers used to pass a content field from documents and groundtruths to an executor and add the evaluation value

    .. note::
        - Valid fields:
                    ['id', 'level_name', 'parent_id', 'text', 'mime_type', 'uri', 'modality']
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
        """Load the ground truth.

        :param args: unused
        :param kwargs: unused
        """
        miss_idx = []  #: missed hit results, some documents may not have groundtruth and thus will be removed
        for idx, doc in enumerate(self.docs):
            serialized_groundtruth = self.exec_fn(doc.id)
            if serialized_groundtruth:
                self.req.groundtruths.append(Document(serialized_groundtruth))
            else:
                miss_idx.append(idx)
        # delete non-existed matches in reverse
        for j in reversed(miss_idx):
            del self.docs[j]
