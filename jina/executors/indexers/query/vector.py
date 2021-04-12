from typing import Generator

import numpy as np

from jina.executors.indexers.dump import import_vectors
from jina.executors.indexers.query import BaseQueryIndexer
from jina.executors.indexers.vector import NumpyIndexer


class NumpyQueryIndexer(NumpyIndexer, BaseQueryIndexer):
    """An exhaustive vector indexers implemented with numpy and scipy.

    .. note::
        Metrics other than `cosine` and `euclidean` requires ``scipy`` installed.

    :param metric: The distance metric to use. `braycurtis`, `canberra`, `chebyshev`, `cityblock`, `correlation`,
                    `cosine`, `dice`, `euclidean`, `hamming`, `jaccard`, `jensenshannon`, `kulsinski`,
                    `mahalanobis`,
                    `matching`, `minkowski`, `rogerstanimoto`, `russellrao`, `seuclidean`, `sokalmichener`,
                    `sokalsneath`, `sqeuclidean`, `wminkowski`, `yule`.
    :param backend: `numpy` or `scipy`, `numpy` only supports `euclidean` and `cosine` distance
    :param compress_level: compression level to use
    """

    def _load_dump(self, dump_path):
        """Load the dump at the path

        :param dump_path: the path of the dump"""
        ids, vecs = import_vectors(dump_path, str(self.pea_id))
        self._add(ids, vecs)
        self.write_handler.flush()
        self.write_handler.close()
        self.handler_mutex = False
        self.is_handler_loaded = False
        test_vecs = np.array([np.random.random(self.num_dim)], dtype=self.dtype)
        assert self.query(test_vecs, 1) is not None

    def _add(self, keys: Generator, vectors: Generator, *args, **kwargs) -> None:
        """Add the embeddings and document ids to the index.

        NOTE::

            This replaces the parent class' `_add` since we
            need to adapt to use Generators from the dump loading

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param vectors: embeddings
        :param args: not used
        :param kwargs: not used
        """
        keys = np.array(list(keys), (np.str_, self.key_length))
        vectors_nr = 0
        for vector in vectors:
            if not getattr(self, 'num_dim', None):
                self.num_dim = vector.shape[0]
                self.dtype = vector.dtype.name
            self.write_handler.write(vector.tobytes())
            vectors_nr += 1

        if vectors_nr != keys.shape[0]:
            raise ValueError(
                f'Different number of vectors and keys. {vectors_nr} vectors and {len(keys)} keys. Validate your dump'
            )

        self.valid_indices = np.concatenate(
            (self.valid_indices, np.full(len(keys), True))
        )
        self.key_bytes += keys.tobytes()
        self._size += keys.shape[0]
