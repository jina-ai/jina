from ..helper import extract_chunks, array2blob


def handler_encode_doc(exec_fn, pea, req, *args, **kwargs):
    """Extract the chunk-level content from documents and call executor and do encoding

    It requires ``ctx`` has :class:`jina.executors.encoders.BaseEncoder` equipped.
    """
    contents, chunk_pts, no_chunk_docs, bad_chunk_ids = extract_chunks(req.docs, embedding=False)

    if no_chunk_docs:
        pea.logger.warning('these docs contain no chunk: %s' % no_chunk_docs)

    if bad_chunk_ids:
        pea.logger.warning('these bad chunks can not be added: %s' % bad_chunk_ids)

    if chunk_pts:
        try:
            embeds = exec_fn(contents)
            if len(chunk_pts) != embeds.shape[0]:
                pea.logger.error(
                    'mismatched %d chunks and a %s shape embedding, '
                    'the first dimension must be the same' % (len(chunk_pts), embeds.shape))
            for c, emb in zip(chunk_pts, embeds):
                c.embedding.CopyFrom(array2blob(emb))
        except Exception as ex:
            pea.logger.error(ex, exc_info=True)
            pea.logger.warning('encoder service throws an exception, '
                               'the sequel pipeline may not work properly')
