__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import BaseExecutableDriver
from .helper import extract_chunks, array2pb


class BaseEncodeDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'encode', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class EncodeDriver(BaseEncodeDriver):
    """Extract the chunk-level content from documents and call executor and do encoding
    """

    def __call__(self, *args, **kwargs):
        contents, chunk_pts, no_chunk_docs, bad_chunk_ids = extract_chunks(self.req.docs,
                                                                           self.req.filter_by,
                                                                           embedding=False)

        if no_chunk_docs:
            self.logger.warning('these docs contain no chunk: %s' % no_chunk_docs)

        if bad_chunk_ids:
            self.logger.warning('these bad chunks can not be added: %s' % bad_chunk_ids)

        if chunk_pts:
            try:
                embeds = self.exec_fn(contents)
                if len(chunk_pts) != embeds.shape[0]:
                    self.logger.error(
                        'mismatched %d chunks and a %s shape embedding, '
                        'the first dimension must be the same' % (len(chunk_pts), embeds.shape))
                for c, emb in zip(chunk_pts, embeds):
                    c.embedding.CopyFrom(array2pb(emb))
            except Exception as ex:
                self.logger.error(ex, exc_info=True)
                self.logger.warning('encoder driver throws an exception, '
                                    'the sequel pipeline may not work properly')
