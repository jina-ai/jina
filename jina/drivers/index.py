__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

import numpy as np

from . import BaseExecutableDriver
from .helper import extract_docs

if False:
    from ..proto import jina_pb2

class BaseIndexDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'add', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class VectorIndexDriver(BaseIndexDriver):
    """Extract chunk-level embeddings and add it to the executor
    """

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        embed_vecs, chunk_pts, no_chunk_docs, bad_chunk_ids = extract_docs(docs, embedding=True)

        if no_chunk_docs:
            self.pea.logger.warning(f'these docs contain no chunk: {no_chunk_docs}')

        if bad_chunk_ids:
            self.pea.logger.warning(f'these bad chunks can not be added: {bad_chunk_ids}')

        if chunk_pts:
            self.exec_fn(np.array([c.id for c in chunk_pts]), np.stack(embed_vecs))


class KVIndexDriver(BaseIndexDriver):
    """Serialize the documents/chunks in the request to key-value JSON pairs and write it using the executor
    """

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        self.exec_fn(docs)
