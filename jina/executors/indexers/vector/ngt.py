__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

import numpy as np

from .numpy import NumpyIndexer


class NGTIndexer(NumpyIndexer):
    """NGT powered vector indexer

    For more information about the NGT supported parameters and installation problems, please consult:
        - https://github.com/yahoojapan/NGT

    .. note::
        NGT package dependency is only required at the query time.
        Quick Install : pip install ngt
    """

    def __init__(self, state: str ='index',index_path: str = '/tmp/jina/index',  metric: str = 'L2', *args, **kwargs):
        """
        Initialize an NGT Indexer

        :param state: If indexing is already done , no need to index again.
                      Set "index" to index again (If new data has been added)
                      Set "load" to load from pre indexed file

        :param index_path: path to store indexing by NGT. Option to persist. Should be ta folder
                          Faster than indexing again if no new data has been indexed.

        :param state: Should be one of {L1,L2,Hamming,Jaccard,Angle,Normalized Angle,Cosine,Normalized Cosine}
        """
        super().__init__(*args, **kwargs)
        self.index_path = index_path
        self.metric = metric
        self.state= state

    def get_query_handler(self):
        """Index all vectors , if already indexed return NGT Index handle """

        import ngtpy
        if self.state=='index':
            vecs = super().get_query_handler()
            if vecs is not None:
                ngtpy.create(path=self.index_path, dimension=self.num_dim, distance_type=self.metric)
                _index = ngtpy.Index(self.index_path)
                _index.batch_insert(vecs)
                _index.save()
                _index.close()
                return ngtpy.Index(self.index_path)
            else:
                return None
        elif self.state=='load':
            return ngtpy.Index(self.index_path)
        else:
            raise ValueError('state should either be index or load')

    def query(self, keys: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        if keys.dtype != np.float32:
            raise ValueError('vectors should be ndarray of float32')

        index=self.query_handler
        dist = list()
        idx = list()
        for key in keys:
            result = index.search(key, size=top_k,)
            idx.append(result[0])
            dist.append(result[1])

        return self.int2ext_key[np.array(idx)], np.array(dist)