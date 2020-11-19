__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterator

import numpy as np

from . import BaseExecutableDriver
from ..types.document.helper import extract_embedding

if False:
    from ..types.document import Document


class BaseIndexDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`add` by default """

    def __init__(self, executor: str = None, method: str = 'add', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class VectorIndexDriver(BaseIndexDriver):
    """Extract chunk-level embeddings and add it to the executor
    """

    def _apply_all(self, docs: Iterator['Document'], *args, **kwargs) -> None:
        embed_vecs, docs_pts, bad_doc_ids = extract_embedding(docs)

        if bad_doc_ids:
            self.pea.logger.warning(f'these bad docs can not be added: {bad_doc_ids}')

        if docs_pts:
            self.exec_fn(np.array([doc.id_in_hash for doc in docs_pts]), np.stack(embed_vecs))


class KVIndexDriver(BaseIndexDriver):
    """Serialize the documents/chunks in the request to key-value JSON pairs and write it using the executor
    """

    def _apply_all(self, docs: Iterator['Document'], *args, **kwargs) -> None:
        keys = [doc.id_in_hash for doc in docs]
        values = [doc.SerializeToString() for doc in docs]
        self.exec_fn(keys, values)
