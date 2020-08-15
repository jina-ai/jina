__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from . import BaseExecutableDriver, QuerySetReader
from .helper import extract_docs

if False:
    from ..proto import jina_pb2


class BaseSearchDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'query', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)
        self._is_apply = False


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


class VectorSearchDriver(QuerySetReader, BaseSearchDriver):
    """Extract chunk-level embeddings from the request and use the executor to query it

    """

    def __init__(self, top_k: int = 50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._top_k = top_k

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        embed_vecs, doc_pts, bad_doc_ids = extract_docs(docs, embedding=True)

        if bad_doc_ids:
            self.logger.warning(f'these bad docs can not be added: {bad_doc_ids}')

        if doc_pts:
            idx, dist = self.exec_fn(embed_vecs, top_k=self.top_k)
            op_name = self.exec.__class__.__name__
            for doc, topks, scores in zip(doc_pts, idx, dist):
                for match_id, score in zip(topks, scores):
                    r = doc.matches.add()
                    r.level_depth = doc.level_depth
                    r.id = match_id
                    r.score.ref_id = doc.id
                    r.score.value = score
                    r.score.op_name = op_name
