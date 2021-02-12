__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple, Dict, Any

import numpy as np

from . import BaseRecursiveDriver

if False:
    from ..types.document import Document
    from ..types.sets import DocumentSet


class ReduceAllDriver(BaseRecursiveDriver):
    """:class:`ReduceAllDriver` merges chunks/matches from all requests, recursively.

    .. note::

        It uses the last request as a reference.
    """

    def __init__(self, traversal_paths: Tuple[str] = ('c',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        # all pointers of the docs, provide the weak ref to all docs in partial reqs
        self.doc_pointers = {}  # type: Dict[str, Any]
        self._traverse_apply(self.docs, *args, **kwargs)
        self.doc_pointers.clear()

    def _apply_root(self, docs: 'DocumentSet', field: str, *args, **kwargs):
        docs = []
        for doc in self.docs:
            docs.append(doc)
        request = self.msg.request
        request.body.ClearField(field)
        request.docs.extend(docs)

    def _apply_all(
            self,
            docs: 'DocumentSet',
            context_doc: 'Document',
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
            docs: 'DocumentSet',
            context_doc: 'Document',
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
        # all pointers of the docs, provide the weak ref to all docs in partial reqs
        self.doc_pointers = {}  # type: Dict[str, Any]
        self._traverse_apply(self.docs, *args, **kwargs)
        self._traverse_apply(self.req.docs, concatenate=True, *args, **kwargs)
        self.doc_pointers.clear()

    def _apply_all(
            self,
            docs: 'DocumentSet',
            context_doc: 'Document',
            field: str,
            concatenate: bool = False,
            *args,
            **kwargs):
        doc = context_doc
        if concatenate:
            doc.embedding = np.concatenate(self.doc_pointers[doc.id], axis=0)
        else:
            if doc.id not in self.doc_pointers:
                self.doc_pointers[doc.id] = [doc.embedding]
            else:
                self.doc_pointers[doc.id].append(doc.embedding)
