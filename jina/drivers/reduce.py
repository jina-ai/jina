__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple, Iterable

from collections import defaultdict

import numpy as np

from . import ContextAwareRecursiveMixin, BaseRecursiveDriver, FlatRecursiveMixin
from ..types.sets import ChunkSet, MatchSet, DocumentSet


class ReduceAllDriver(ContextAwareRecursiveMixin, BaseRecursiveDriver):
    """:class:`ReduceAllDriver` merges chunks/matches from all requests, recursively.

    .. note::

        It uses the last request as a reference.
    """

    def __init__(self, traversal_paths: Tuple[str] = ('c',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_root(self, docs):
        request = self.msg.request
        request.body.ClearField('docs')
        request.docs.extend(docs)

    def _apply_all(
        self, doc_sequences: Iterable['DocumentSet'], *args, **kwargs
    ) -> None:
        doc_pointers = {}
        for docs in doc_sequences:
            if isinstance(docs, (ChunkSet, MatchSet)):
                context_id = docs.reference_doc.id
                if context_id not in doc_pointers:
                    doc_pointers[context_id] = docs.reference_doc
                else:
                    if isinstance(docs, ChunkSet):
                        doc_pointers[context_id].chunks.extend(docs)
                    else:
                        doc_pointers[context_id].matches.extend(docs)
            else:
                self._apply_root(docs)


class CollectEvaluationDriver(FlatRecursiveMixin, BaseRecursiveDriver):
    """Merge all evaluations into one, grouped by ``doc.id`` """

    def __init__(self, traversal_paths: Tuple[str] = ('r',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        doc_pointers = {}
        for doc in docs:
            if doc.id not in doc_pointers:
                doc_pointers[doc.id] = doc.evaluations
            else:
                doc_pointers[doc.id].extend(doc.evaluations)


class ConcatEmbedDriver(BaseRecursiveDriver):
    """Concat all embeddings into one, grouped by ``doc.id`` """

    def __init__(self, traversal_paths: Tuple[str] = ('r',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        """Performs the concatenation of all embeddings in `self.docs`.

        :param args: args not used. Only for complying with parent class interface.
        :param kwargs: kwargs not used. Only for complying with parent class interface.
        """
        all_documents = self.docs.traverse_flatten(self._traversal_paths)
        doc_pointers = self._collect_embeddings(all_documents)

        last_request_documents = self.req.docs.traverse_flatten(self._traversal_paths)
        self._concat_apply(last_request_documents, doc_pointers)

    def _collect_embeddings(self, docs: 'DocumentSet'):
        doc_pointers = defaultdict(list)
        for doc in docs:
            doc_pointers[doc.id].append(doc.embedding)
        return doc_pointers

    def _concat_apply(self, docs, doc_pointers):
        for doc in docs:
            doc.embedding = np.concatenate(doc_pointers[doc.id], axis=0)
