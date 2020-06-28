__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import BaseNumpyIndexer
from .annoy import AnnoyIndexer
from .faiss import FaissIndexer
from .nmslib import NmslibIndexer
from .numpy import NaiveIndexer
from .sptag import SptagIndexer


class VectorIndexer(BaseNumpyIndexer):
    def __init__(self, backend: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = backend
        self._args, self._kwargs = args, kwargs

    def post_init(self):
        super().post_init()
        if self.backend in {'numpy', 'scipy'}:
            idx_cls = NaiveIndexer
        elif self.backend == 'annoy':
            idx_cls = AnnoyIndexer
        elif self.backend == 'sptag':
            idx_cls = SptagIndexer
        elif self.backend == 'nmslib':
            idx_cls = NmslibIndexer
        elif self.backend == 'faiss':
            idx_cls = FaissIndexer
        else:
            raise ValueError(f'{self.backend} is not supported')
        _indexer = idx_cls(backend=self.backend, *self._args, **self._kwargs)
        # copy deserialized info to _indexer, use them to build correct q/w handler
        _indexer.__dict__.update(self.__dict__)
        # manually trigger q/w handler
        _indexer.query_handler
        _indexer.write_handler
        # copy all things back and replace "self"
        self.__dict__.update(_indexer.__dict__)
        self.query = _indexer.query
