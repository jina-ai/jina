from . import BaseExecutableDriver
from .helper import extract_chunks


class DocPbSearchDriver(BaseExecutableDriver):
    """Fill in the doc-level top-k results using the :class:`jina.executors.indexers.meta.BasePbIndexer`

    """

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            for tk in d.topk_results:
                tk.match_doc.CopyFrom(self.exec_fn(tk.match_doc.doc_id))


class ChunkPbSearchDriver(BaseExecutableDriver):
    """Fill in the chunk-level top-k results using the :class:`jina.executors.indexers.meta.BasePbIndexer`

    """

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            for c in d.chunks:
                for k in c.topk_results:
                    k.match_chunk.CopyFrom(self.exec_fn(k.match_chunk.chunk_id))


class ChunkSearchDriver(BaseExecutableDriver):
    """Extract chunk-level embeddings from the request and use the executor to query it

    """

    def __call__(self, *args, **kwargs):
        embed_vecs, chunk_pts, no_chunk_docs, bad_chunk_ids = extract_chunks(self.req.docs, embedding=True)

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
