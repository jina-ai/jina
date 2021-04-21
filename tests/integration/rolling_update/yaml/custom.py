from typing import Tuple, Iterable, Optional

import numpy as np


from jina.executors.indexers.vector import NumpyIndexer


class MockVectorIndexer(NumpyIndexer):
    def query(
        self, vectors: 'np.ndarray', top_k: int, *args, **kwargs
    ) -> Tuple['np.ndarray', 'np.ndarray']:
        return np.array([[0]]), np.array([[self.replica_id]])

    def query_by_key(
        self, keys: Iterable[str], *args, **kwargs
    ) -> Optional['np.ndarray']:
        return np.array([[0] * 5])
