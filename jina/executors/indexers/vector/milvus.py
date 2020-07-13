__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

import numpy as np

from . import BaseVectorIndexer
from .milvus import MilvusDBHandler


class MilvusIndexer(BaseVectorIndexer):

    def __init__(self, host: str, port: int, collection_name: str, index_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.index_type = index_type

    def __post_init__(self):
        super().post_init()
        self.milvus = MilvusDBHandler(self.host, self.port, self.collection_name)

    def get_query_handler(self):
        db_handler = self.milvus.connect()
        db_handler.build_index(self.index_type, None)
        return db_handler

    def get_add_handler(self):
        return self.milvus.connect()

    def get_create_handler(self):
        return self.milvus.connect()

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        self.validate_key_vector_shapes(keys, vectors)
        self.write_handler.insert(keys, vectors)

    def query(self, vectors: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        dist, ids = self.query_handler.search(vectors, top_k, *args, **kwargs)
        return ids, dist
