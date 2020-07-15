__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from . import BaseExecutableDriver
from .helper import extract_chunks
from ..proto.jina_pb2 import ScoredResult

if False:
    from ..proto import jina_pb2


class BaseSearchDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'query', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


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

    def __init__(self, level: str, *args, **kwargs):
        """

        :param level: index level "chunk" or "doc", or "all"
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.level = level

    def apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        hit_sr = []  #: hited scored results, not some search may not ends with result. especially in shards
        for tk in doc.topk_results:
            r = self.exec_fn(tk.match.id)
            if r:
                sr = ScoredResult()
                sr.score.CopyFrom(tk.score)
                sr.match.CopyFrom(r)
                hit_sr.append(sr)
        doc.ClearField('topk_results')
        doc.topk_results.extend(hit_sr)


# DocKVSearchDriver, no need anymore as there is no differnce between chunk and doc
# DocKVSearchDriver, no need anymore as there is no differnce between chunk and doc

class VectorSearchDriver(BaseSearchDriver):
    """Extract chunk-level embeddings from the request and use the executor to query it

    """

    def apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        embed_vecs, chunk_pts, no_chunk_docs, bad_chunk_ids = extract_chunks(docs,
                                                                             embedding=True)

        if no_chunk_docs:
            self.logger.warning(f'these docs contain no chunk: {no_chunk_docs}')

        if bad_chunk_ids:
            self.logger.warning(f'these bad chunks can not be added: {bad_chunk_ids}')

        if chunk_pts:
            idx, dist = self.exec_fn(embed_vecs, top_k=self.req.top_k)
            op_name = self.exec.__class__.__name__
            for c, topks, scs in zip(chunk_pts, idx, dist):
                for m, s in zip(topks, scs):
                    r = c.topk_results.add()
                    r.match.id = m
                    r.score.value = s
                    r.score.op_name = op_name
