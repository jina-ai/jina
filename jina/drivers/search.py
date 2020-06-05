__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import BaseExecutableDriver
from .helper import extract_chunks
from ..proto.jina_pb2 import ScoredResult


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

    def __call__(self, *args, **kwargs):
        if self.level == 'doc':
            for d in self.req.docs:
                self._update_topk_docs(d)
        elif self.level == 'chunk':
            for d in self.req.docs:
                for c in d.chunks:
                    self._update_topk_chunks(c)
        elif self.level == 'all':
            for d in self.req.docs:
                self._update_topk_docs(d)
                for c in d.chunks:
                    self._update_topk_chunks(c)
        else:
            raise TypeError(f'level={self.level} is not supported, must choose from "chunk" or "doc" ')

    def _update_topk_docs(self, d):
        hit_sr = []  #: hited scored results, not some search may not ends with result. especially in shards
        for tk in d.topk_results:
            r = self.exec_fn(f'd{tk.match_doc.doc_id}')
            if r:
                sr = ScoredResult()
                sr.score.CopyFrom(tk.score)
                sr.match_doc.CopyFrom(r)
                hit_sr.append(sr)
        d.ClearField('topk_results')
        d.topk_results.extend(hit_sr)

    def _update_topk_chunks(self, c):
        hit_sr = []  #: hited scored results, not some search may not ends with result. especially in shards
        for tk in c.topk_results:
            r = self.exec_fn(f'c{tk.match_chunk.chunk_id}')
            if r:
                sr = ScoredResult()
                sr.score.CopyFrom(tk.score)
                sr.match_chunk.CopyFrom(r)
                hit_sr.append(sr)
        c.ClearField('topk_results')
        c.topk_results.extend(hit_sr)


class DocKVSearchDriver(KVSearchDriver):
    """A shortcut to :class:`KVSearchDriver` with ``level=doc``"""

    def __init__(self, level: str = 'doc', *args, **kwargs):
        super().__init__(level, *args, **kwargs)


class ChunkKVSearchDriver(KVSearchDriver):
    """A shortcut to :class:`KVSearchDriver` with ``level=chunk``"""

    def __init__(self, level: str = 'chunk', *args, **kwargs):
        super().__init__(level, *args, **kwargs)


class VectorSearchDriver(BaseSearchDriver):
    """Extract chunk-level embeddings from the request and use the executor to query it

    """

    def __call__(self, *args, **kwargs):
        embed_vecs, chunk_pts, no_chunk_docs, bad_chunk_ids = extract_chunks(self.req.docs, self.req.filter_by,
                                                                             embedding=True)

        if no_chunk_docs:
            self.logger.warning('these docs contain no chunk: %s' % no_chunk_docs)

        if bad_chunk_ids:
            self.logger.warning('these bad chunks can not be added: %s' % bad_chunk_ids)

        idx, dist = self.exec_fn(embed_vecs, top_k=self.req.top_k)
        op_name = self.exec.__class__.__name__
        for c, topks, scs in zip(chunk_pts, idx, dist):
            for m, s in zip(topks, scs):
                r = c.topk_results.add()
                r.match_chunk.chunk_id = m
                r.score.value = s
                r.score.op_name = op_name
