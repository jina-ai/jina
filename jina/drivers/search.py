__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable, Tuple

from . import (
    BaseExecutableDriver,
    QuerySetReader,
    FlatRecursiveMixin,
    ContextAwareRecursiveMixin,
)
from ..types.document import Document
from ..types.score import NamedScore

if False:
    from ..types.sets import DocumentSet


class BaseSearchDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(
        self,
        executor: str = None,
        method: str = 'query',
        traversal_paths: Tuple[str] = ('r', 'c'),
        *args,
        **kwargs,
    ):
        super().__init__(
            executor, method, traversal_paths=traversal_paths, *args, **kwargs
        )


class KVSearchDriver(ContextAwareRecursiveMixin, BaseSearchDriver):
    """Fill in the results using the :class:`jina.executors.indexers.meta.BinaryPbIndexer`

    .. warning::
        This driver runs a query for each document.
        This may not be very efficient, as the total number of queries grows cubic with the number of documents, chunks
        per document and top-k.

            - traversal_paths = ['m'] => D x K
            - traversal_paths = ['r'] => D
            - traversal_paths = ['cm'] => D x C x K
            - traversal_paths = ['m', 'cm'] => D x K + D x C x K

        where:
            - D is the number of queries
            - C is the number of chunks per document
            - K is the top-k
    """

    def __init__(
        self,
        is_update: bool = True,
        traversal_paths: Tuple[str] = ('m'),
        *args,
        **kwargs,
    ):
        """Construct the driver.

        :param is_update: when set to true the retrieved docs are merged into current message;
            otherwise, the retrieved Document overrides the existing Document
        :param traversal_paths: traversal paths for the driver
        :param *args: *args for super
        :param **kwargs: **kwargs for super
        """
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)
        self._is_update = is_update

    def _apply_all(
        self, doc_sequences: Iterable['DocumentSet'], *args, **kwargs
    ) -> None:
        for docs in doc_sequences:
            miss_idx = (
                []
            )  #: missed hit results, some search may not end with results. especially in shards
            for idx, retrieved_doc in enumerate(docs):
                serialized_doc = self.exec_fn(retrieved_doc.id)
                if serialized_doc:
                    r = Document(serialized_doc)
                    if self._is_update:
                        retrieved_doc.update(r)
                    else:
                        retrieved_doc.CopyFrom(r)
                else:
                    miss_idx.append(idx)
            # delete non-existed matches in reverse
            for j in reversed(miss_idx):
                del docs[j]


class VectorFillDriver(FlatRecursiveMixin, QuerySetReader, BaseSearchDriver):
    """Fill in the embedding by their document id."""

    def __init__(
        self, executor: str = None, method: str = 'query_by_key', *args, **kwargs
    ):
        super().__init__(executor, method, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        embeds = self.exec_fn([d.id for d in docs])
        for doc, embedding in zip(docs, embeds):
            doc.embedding = embedding


class VectorSearchDriver(FlatRecursiveMixin, QuerySetReader, BaseSearchDriver):
    """Extract embeddings from the request for the executor to query."""

    def __init__(self, top_k: int = 50, fill_embedding: bool = False, *args, **kwargs):
        """Construct the driver.

        :param top_k: top-k document ids to retrieve
        :param fill_embedding: fill in the embedding of the corresponding doc,
                this requires the executor to implement :meth:`query_by_key`
        :param *args: *args for super
        :param **kwargs: **kwargs for super
        """
        super().__init__(*args, **kwargs)
        self._top_k = top_k
        self._fill_embedding = fill_embedding

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        embed_vecs, doc_pts = docs.all_embeddings

        if not doc_pts:
            return

        fill_fn = getattr(self.exec, 'query_by_key', None)
        if self._fill_embedding and not fill_fn:
            self.logger.warning(
                f'"fill_embedding=True" but {self.exec} does not have "query_by_key" method'
            )

        idx, dist = self.exec_fn(embed_vecs, top_k=int(self.top_k))

        op_name = self.exec.__class__.__name__
        for doc, topks, scores in zip(doc_pts, idx, dist):

            topk_embed = (
                fill_fn(topks)
                if (self._fill_embedding and fill_fn)
                else [None] * len(topks)
            )
            for numpy_match_id, score, vec in zip(topks, scores, topk_embed):
                m = Document(id=numpy_match_id)
                m.score = NamedScore(op_name=op_name, value=score)
                r = doc.matches.append(m)
                if vec is not None:
                    r.embedding = vec
