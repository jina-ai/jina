__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

import numpy as np

from .numpy import NumpyIndexer


class SptagIndexer(NumpyIndexer):
    """SPTAG powered vector indexer

    For SPTAG installation and python API usage, please consult:

        - https://github.com/microsoft/SPTAG/blob/master/Dockerfile
        - https://github.com/microsoft/SPTAG/blob/master/docs/Tutorial.ipynb
        - https://github.com/microsoft/SPTAG

    .. note::
        sptag package dependency is only required at the query time.
    """

    def __init__(self, dist_calc_method: str = 'L2', method: str = 'BKT',
                 num_threads: int = 1,
                 *args, **kwargs):
        """
        Initialize an NmslibIndexer

        :param dist_calc_method: the distance type, currently SPTAG only support Cosine and L2 distances.
        :param method: The index method to use, index Algorithm type (e.g. BKT, KDT), required.
        :param num_threads: The number of threads to use
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.method = method
        self.space = dist_calc_method
        self.num_threads = num_threads

    def get_query_handler(self):
        vecs = super().get_query_handler()
        if vecs is not None:
            import SPTAG

            _index = SPTAG.AnnIndex(self.method, 'Float', vecs.shape[1])

            # Set the thread number to speed up the build procedure in parallel
            _index.SetBuildParam("NumberOfThreads", str(self.num_threads))
            _index.SetBuildParam("DistCalcMethod", self.method)

            if _index.Build(vecs, vecs.shape[0]):
                return _index
        else:
            return None

    def query(self, keys: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        if keys.dtype != np.float32:
            raise ValueError('vectors should be ndarray of float32')

        ret = self.query_handler.Search(keys, top_k)
        idx, dist = zip(*ret)
        return self.int2ext_key[np.array(idx)], np.array(dist)
