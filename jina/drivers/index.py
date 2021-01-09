__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from . import BaseExecutableDriver

if False:
    from ..types.sets import DocumentSet


class BaseIndexDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`add` by default """

    def __init__(self, executor: str = None, method: str = 'add', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class VectorIndexDriver(BaseIndexDriver):
    """Extract chunk-level embeddings and add it to the executor
    """

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        if self._method_name == 'delete':
            self.exec_fn(np.array([int(doc.id) for doc in docs]), None)
        else:
            embed_vecs, docs_pts, bad_docs = docs.all_embeddings
            if bad_docs:
                self.runtime.logger.warning(f'these bad docs can not be added: {bad_docs}')
            if docs_pts:
                self.exec_fn(np.array([int(doc.id) for doc in docs_pts]), np.stack(embed_vecs))


class KVIndexDriver(BaseIndexDriver):
    """Serialize the documents/chunks in the request to key-value JSON pairs and write it using the executor
    """

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        keys = [int(doc.id) for doc in docs]
        values = [doc.SerializeToString() for doc in docs]
        self.exec_fn(keys, values)
