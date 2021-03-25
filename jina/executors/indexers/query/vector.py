from typing import Generator

import numpy as np

from jina.executors.dump import DumpPersistor
from jina.executors.indexers.query import QueryReloadIndexer
from jina.executors.indexers.vector import NumpyIndexer


class QueryNumpyIndexer(NumpyIndexer, QueryReloadIndexer):
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

    def __init__(self, uri_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uri_path = uri_path
        if self.uri_path:
            self.reload(self.uri_path)
        else:
            self.logger.warning(
                f'The indexer does not have any data. Make sure to use ReloadRequest to tell it how to import data...'
            )

    def reload(self, path):
        """This can be a universal dump format(to be defined)
        Or optimized to the Indexer format.

        We first copy to a temporary folder (within workspace?)

        The dump is created by a DumpRequest to the CUD Indexer (SQLIndexer)
        with params:
            formats: universal, Numpy, BinaryPb etc.
            shards: X

        The shards are configured per dump
        """
        print(f'### Np Importing from dump at {path}')
        ids, vecs = DumpPersistor.import_vectors(path, str(self.pea_id))
        self.add(ids, vecs)
        self.write_handler.flush()
        self.write_handler.close()
        self.handler_mutex = False
        self.is_handler_loaded = False
        # TODO warm up here in a cleaner way
        test_vecs = np.array([np.random.random(self.num_dim)], dtype=self.dtype)
        assert self.query(test_vecs, 1) is not None
        print(f'### vec self.size after import: {self.size}')

    def add(self, keys: Generator, vectors: Generator, *args, **kwargs) -> None:
        """Add the embeddings and document ids to the index.

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
