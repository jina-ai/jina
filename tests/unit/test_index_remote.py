import os

import numpy as np

from jina.executors.indexers.vector import NumpyIndexer

cur_dir = os.path.dirname(os.path.abspath(__file__))


def get_result(resp):
    n = []
    for d in resp.search.docs:
        for c in d.chunks:
            n.append([k.id for k in c.matches])
    n = np.array(n)
    # each chunk should return a list of top-100
    np.testing.assert_equal(n.shape[0], 5)
    np.testing.assert_equal(n.shape[1], 100)


class DummyIndexer(NumpyIndexer):
    # the add() function is simply copied from NumpyIndexer
    def add(self, *args, **kwargs):
        pass


class DummyIndexer2(NumpyIndexer):
    # the add() function is simply copied from NumpyIndexer
    def add(self, id: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        if len(vectors.shape) != 2:
            raise ValueError(
                f'vectors shape {vectors.shape} is not valid, expecting "vectors" to have rank of 2'
            )

        if not self.num_dim:
            self.num_dim = vectors.shape[1]
            self.dtype = vectors.dtype.name
        elif self.num_dim != vectors.shape[1]:
            raise ValueError(
                "vectors' shape [%d, %d] does not match with indexers's dim: %d"
                % (vectors.shape[0], vectors.shape[1], self.num_dim)
            )
        elif self.dtype != vectors.dtype.name:
            raise TypeError(
                f"vectors' dtype {vectors.dtype.name} does not match with indexers's dtype: {self.dtype}"
            )
        elif id.shape[0] != vectors.shape[0]:
            raise ValueError(
                'number of key %d not equal to number of vectors %d'
                % (id.shape[0], vectors.shape[0])
            )
        elif self.key_dtype != id.dtype.name:
            raise TypeError(
                f"keys' dtype {id.dtype.name} does not match with indexers keys's dtype: {self.key_dtype}"
            )

        self.write_handler.write(vectors.tobytes())
        self.key_bytes += id.tobytes()
        self.key_dtype = id.dtype.name
        self._size += id.shape[0]
