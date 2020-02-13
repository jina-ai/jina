from ..helper import extract_chunks


def handler_meta_search_doc(exec_fn, pea, req, *args, **kwargs):
    """Fill in the doc-level top-k results using the :class:`jina.executors.indexers.meta.MetaProtoIndexer`

    It requires ``ctx`` has ``MetaProtoIndexer`` equipped.
    """
    for d in req.docs:
        for tk in d.topk_results:
            tk.match_doc.CopyFrom(exec_fn(tk.match_doc.doc_id))


def handler_meta_search_chunk(exec_fn, pea, req, *args, **kwargs):
    """Fill in the chunk-level top-k results using the :class:`jina.executors.indexers.meta.MetaProtoIndexer`

    It requires ``ctx`` has ``MetaProtoIndexer`` equipped.
    """
    for d in req.docs:
        for c in d.chunks:
            for k in c.topk_results:
                k.match_chunk.CopyFrom(exec_fn(k.match_chunk.chunk_id))


def handler_chunk_search(exec_fn, pea, req, *args, **kwargs):
    """Extract chunk-level embeddings from the request and use the executor to query it

    It requires ``ctx`` has :class:`jina.executors.indexers.BaseIndexer` equipped.
    """

    embed_vecs, chunk_pts, no_chunk_docs, bad_chunk_ids = extract_chunks(req.docs, embedding=True)

    if no_chunk_docs:
        pea.logger.warning('these docs contain no chunk: %s' % no_chunk_docs)

    if bad_chunk_ids:
        pea.logger.warning('these bad chunks can not be added: %s' % bad_chunk_ids)

    idx, dist = exec_fn(embed_vecs, top_k=req.top_k)
    op_name = pea.executor.__class__.__name__
    for c, topks, scs in zip(chunk_pts, idx, dist):
        for m, s in zip(topks, scs):
            r = c.topk_results.add()
            r.match_chunk.chunk_id = m
            r.score.value = s
            r.score.op_name = op_name
