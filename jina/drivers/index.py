import numpy as np

from . import BaseExecutorDriver
from .helper import extract_chunks


class ChunkIndexDriver(BaseExecutorDriver):
    """Extract chunk-level embeddings and add it to the executor

    It requires ``ctx`` has :class:`jina.executors.indexers.BaseIndexer` equipped.
    """

    def __call__(self, *args, **kwargs):
        embed_vecs, chunk_pts, no_chunk_docs, bad_chunk_ids = extract_chunks(self.req.docs, embedding=True)

        if no_chunk_docs:
            self.pea.logger.warning('these docs contain no chunk: %s' % no_chunk_docs)

        if bad_chunk_ids:
            self.pea.logger.warning('these bad chunks can not be added: %s' % bad_chunk_ids)

        if chunk_pts:
            self.exec_fn(np.array([c.chunk_id for c in chunk_pts]), np.stack(embed_vecs))


class DocMetaIndexDriver(BaseExecutorDriver):
    """Serialize the documents in the request to JSON and write it using the executor

    It requires ``ctx`` has ``meta_writer`` equipped.
    """

    def __call__(self, *args, **kwargs):
        from google.protobuf.json_format import MessageToJson
        content = {'d%d' % d.doc_id: MessageToJson(d) for d in self.req.docs}
        if content:
            self.exec_fn(content)


class ChunkMetaIndexDriver(BaseExecutorDriver):
    """Serialize all chunks in the request to JSON and write it using the executor

    It requires ``ctx`` has ``meta_writer`` equipped.
    """

    def __call__(self, *args, **kwargs):
        from google.protobuf.json_format import MessageToJson
        content = {'c%d' % c.chunk_id: MessageToJson(c) for d in self.req.docs for c in d.chunks}
        if content:
            self.exec_fn(content)
