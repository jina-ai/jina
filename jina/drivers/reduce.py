__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable, Tuple

import numpy as np

from . import BaseRecursiveDriver
from ..proto import jina_pb2
from ..proto.ndarray.generic import GenericNdArray


class ReduceDriver(BaseRecursiveDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(expect_parts=None, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        """Intentionally override traverse_apply with empty function"""


class ReduceAllDriver(BaseRecursiveDriver):
    """:class:`ReduceAllDriver` merges chunks/matches from all requests, recursively.

    .. note::

        It uses the last request as a reference.
    """

    def __init__(self, traversal_paths: Tuple[str] = ('c',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, expect_parts=None, *args, **kwargs)

    def _apply_all(
            self,
            docs: Iterable['jina_pb2.Document'],
            context_doc: 'jina_pb2.Document',
            field: str,
            *args,
            **kwargs) -> None:
        if context_doc.id not in self.doc_pointers:
            self.doc_pointers[context_doc.id] = context_doc
        else:
            getattr(self.doc_pointers[context_doc.id], field).extend(docs)


class CollectEvaluationDriver(ReduceAllDriver):
    """Merge all evaluations into one, grouped by ``doc.id`` """

    def _apply_all(
            self,
            docs: Iterable['jina_pb2.Document'],
            context_doc: 'jina_pb2.Document',
            field: str,
            *args,
            **kwargs) -> None:
        if context_doc.id not in self.doc_pointers:
            self.doc_pointers[context_doc.id] = context_doc.evaluations
        else:
            self.doc_pointers[context_doc.id].extend(context_doc.evaluations)


class ConcatEmbedDriver(ReduceAllDriver):
    """Concat all embeddings into one, grouped by ```doc.id``` """

    def __call__(self, *args, **kwargs):
        self._traverse_apply(self.docs, *args, **kwargs)
        self._traverse_apply(self.req.docs, concatenate=True, *args, **kwargs)

    def _apply_all(
            self,
            docs: Iterable['jina_pb2.Document'],
            context_doc: 'jina_pb2.Document',
            field: str,
            concatenate: bool = False,
            *args,
            **kwargs):
        doc = context_doc
        if concatenate:
            GenericNdArray(doc.embedding).value = np.concatenate(self.doc_pointers[doc.id], axis=0)
        else:
            if doc.id not in self.doc_pointers:
                self.doc_pointers[doc.id] = [GenericNdArray(doc.embedding).value]
            else:
                self.doc_pointers[doc.id].append(GenericNdArray(doc.embedding).value)

