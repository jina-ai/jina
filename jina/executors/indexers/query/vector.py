from typing import Generator, Iterable

import numpy as np

from jina.executors.dump import import_vectors
from jina.executors.indexers.query import BaseQueryIndexer
from jina.executors.indexers.vector import NumpyIndexer


class QueryNumpyIndexer(NumpyIndexer, BaseQueryIndexer):
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

    def load_dump(self, dump_path):
        """Load the dump at the path

        :param dump_path: the path of the dump"""
        ids, vecs = import_vectors(dump_path, str(self.pea_id))
        self.add(ids, vecs)
        self.write_handler.flush()
        self.write_handler.close()
        self.handler_mutex = False
        self.is_handler_loaded = False
        test_vecs = np.array([np.random.random(self.num_dim)], dtype=self.dtype)
        assert self.query(test_vecs, 1) is not None
        self.initialized = True

    def add(self, keys: Generator, vectors: Generator, *args, **kwargs) -> None:
        """Add the embeddings and document ids to the index.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param vectors: embeddings
        :param args: not used
        :param kwargs: not used
        """
        if self.initialized:
            self.logger.warning(f'Index {self.index_abspath} is write-once')
            return

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

    def update(
        self, keys: Iterable[str], values: Iterable[bytes], *args, **kwargs
    ) -> None:
        """Disabled


        .. # noqa: DAR101
        """
        self.logger.warning(f'Index {self.index_abspath} is write-once')

    def delete(self, keys: Iterable[str], *args, **kwargs) -> None:
        """Disabled


        .. # noqa: DAR101
        """
        self.logger.warning(f'Index {self.index_abspath} is write-once')
