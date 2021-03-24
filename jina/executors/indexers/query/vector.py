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
            self.import_uri_path(self.uri_path)
        else:
            self.logger.warning(
                f'The indexer does not have any data. Make sure to use ReloadRequest to tell it how to import data...'
            )

    def import_uri_path(self, path):
        """This can be a universal dump format(to be defined)
        Or optimized to the Indexer format.

        We first copy to a temporary folder (within workspace?)

        The dump is created by a DumpRequest to the CUD Indexer (SQLIndexer)
        with params:
            formats: universal, Numpy, BinaryPb etc.
            shards: X

        The shards are configured per dump
        """
        print(f'### Importing from dump at {path}')
        data = DumpPersistor.import_vectors(path)
        ids = np.array(list(data[0]))
        vecs = np.array(list(data[1]))
        print(f'{vecs=}')
        self.add(ids, vecs)
        self.write_handler.flush()
        self.write_handler.close()
        self.handler_mutex = False
        self.is_handler_loaded = False
        # TODO warm up here in a cleaner way
        assert self.query(vecs[:1], 1) is not None
        print(f'### vec self.size after import: {self.size}')
