import numpy as np

from ..helper import extract_chunks


def handler_chunk_index(exec_fn, pea, req, *args, **kwargs):
    """Extract chunk-level embeddings and add it to the executor

    It requires ``ctx`` has :class:`jina.executors.indexers.BaseIndexer` equipped.
    """

    embed_vecs, chunk_pts, no_chunk_docs, bad_chunk_ids = extract_chunks(req.docs, embedding=True)

    if no_chunk_docs:
        pea.logger.warning('these docs contain no chunk: %s' % no_chunk_docs)

    if bad_chunk_ids:
        pea.logger.warning('these bad chunks can not be added: %s' % bad_chunk_ids)

    if chunk_pts:
        exec_fn(np.array([c.chunk_id for c in chunk_pts]), np.stack(embed_vecs))


def handler_meta_index_doc(exec_fn, pea, req, *args, **kwargs):
    """Serialize the documents in the request to JSON and write it using the executor

    It requires ``ctx`` has ``meta_writer`` equipped.
    """
    from google.protobuf.json_format import MessageToJson
    content = {'d%d' % d.doc_id: MessageToJson(d) for d in req.docs}
    if content:
        exec_fn(content)


def handler_meta_index_chunk(exec_fn, pea, req, *args, **kwargs):
    """Serialize all chunks in the request to JSON and write it using the executor

    It requires ``ctx`` has ``meta_writer`` equipped.
    """
    from google.protobuf.json_format import MessageToJson
    content = {'c%d' % c.chunk_id: MessageToJson(c) for d in req.docs for c in d.chunks}
    if content:
        exec_fn(content)
