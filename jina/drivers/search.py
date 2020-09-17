__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from . import BaseExecutableDriver, QuerySetReader
from .helper import extract_docs, array2pb

if False:
    from ..proto import jina_pb2


class BaseSearchDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'query', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)
        self._is_apply = False
        # search driver recursion apply in pre-order
        self.recursion_order = 'pre'


class KVSearchDriver(BaseSearchDriver):
    """Fill in the doc/chunk-level top-k results using the :class:`jina.executors.indexers.meta.BasePbIndexer`

    .. warning::
        This driver loops over all chunk/chunk's top-K results, each step fires a query.
        This may not be very efficient, as the total number of queries depends on ``level``

             - ``level=chunk``: D x C x K
             - ``level=doc``: D x K
             - ``level=all``: D x C x K

        where:
            - D is the number of queries
            - C is the number of chunks per query/doc
            - K is the top-k
    """

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        miss_idx = []  #: missed hit results, some search may not end with results. especially in shards
        for idx, retrieved_doc in enumerate(docs):
            r = self.exec_fn(retrieved_doc.id)
            if r:
                retrieved_doc.MergeFrom(r)
            else:
                miss_idx.append(idx)

        # delete non-existed matches in reverse
        for j in reversed(miss_idx):
            del docs[j]


class VectorFillDriver(QuerySetReader, BaseSearchDriver):
    """ Fill in the embedding by their doc id
    """

    def __init__(self, executor: str = None, method: str = 'query_by_id', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        embeds = self.exec_fn([d.id for d in docs])
        for doc, embedding in zip(docs, embeds):
            doc.embedding.CopyFrom(array2pb(embedding))


class VectorSearchDriver(QuerySetReader, BaseSearchDriver):
    """Extract chunk-level embeddings from the request and use the executor to query it

    """

    def __init__(self, top_k: int = 50, fill_embedding: bool = False, *args, **kwargs):
        """

        :param top_k: top-k doc id to retrieve
        :param fill_embedding: fill in the embedding of the corresponding doc,
                this requires the executor to implement :meth:`query_by_id`
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self._top_k = top_k
        self._fill_embedding = fill_embedding

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        embed_vecs, doc_pts, bad_doc_ids = extract_docs(docs, embedding=True)

        fill_fn = getattr(self.exec, 'query_by_id', None)
        if self._fill_embedding and not fill_fn:
            self.logger.warning(f'"fill_embedding=True" but {self.exec} does not have "query_by_id" method')

        if doc_pts:
            if bad_doc_ids:
                self.logger.warning(f'these bad docs can not be added: {bad_doc_ids}')
            idx, dist = self.exec_fn(embed_vecs, top_k=int(self.top_k))
            op_name = self.exec.__class__.__name__
            for doc, topks, scores in zip(doc_pts, idx, dist):

                topk_embed = fill_fn(topks) if (self._fill_embedding and fill_fn) else [None] * len(topks)

                for match_id, score, vec in zip(topks, scores, topk_embed):
                    r = doc.matches.add()
                    r.id = match_id
                    r.adjacency = doc.adjacency + 1
                    r.score.ref_id = doc.id
                    r.score.value = score
                    r.score.op_name = op_name
                    if vec is not None:
                        r.embedding.CopyFrom(array2pb(vec))
