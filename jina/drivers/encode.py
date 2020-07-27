__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from . import BaseExecutableDriver
from .helper import extract_docs, array2pb

if False:
    from ..proto import jina_pb2


class BaseEncodeDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'encode', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class EncodeDriver(BaseEncodeDriver):
    """Extract the chunk-level content from documents and call executor and do encoding
    """

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        contents, chunk_pts, bad_chunk_ids = extract_docs(docs,
                                                          embedding=False)

        if bad_chunk_ids:
            self.logger.warning(f'these bad chunks can not be added: {bad_chunk_ids}')

        if chunk_pts:
            embeds = self.exec_fn(contents)
            if len(chunk_pts) != embeds.shape[0]:
                self.logger.error(
                    'mismatched %d chunks and a %s shape embedding, '
                    'the first dimension must be the same' % (len(chunk_pts), embeds.shape))
            for c, emb in zip(chunk_pts, embeds):
                c.embedding.CopyFrom(array2pb(emb))


class UnaryEncodeDriver(EncodeDriver):
    """The :class:`UnaryEncodeDriver` extracts the chunk-level content from documents and copies
        the same content to the embedding
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._method_name = None
        self._exec_fn = lambda x: x
