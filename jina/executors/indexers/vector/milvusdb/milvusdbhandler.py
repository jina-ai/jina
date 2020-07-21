__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np
from functools import reduce
import operator
from milvus import Milvus, IndexType
from jina.logging.base import get_logger
from jina.excepts import MilvusDBException


class MilvusDBHandler:
    """Milvus DB handler
        This class is intended to abstract the access and communication with external MilvusDB from Executors

        For more information about Milvus:
            - https://github.com/milvus-io/milvus/
    """

    index_types_map = {
        'Flat': IndexType.FLAT,
        'IVF,Flat': IndexType.IVFLAT,
        'IVF,SQ8': IndexType.IVF_SQ8,
        'RNSG': IndexType.RNSG,
        'IVF,SQ8H': IndexType.IVF_SQ8H,
        'IVF,PQ': IndexType.IVF_PQ,
        'HNSW': IndexType.IVF_PQ,
        'Annoy': IndexType.ANNOY
    }

    class MilvusDBInserter:
        """Milvus DB Inserter
            This class is an inner class and provides a context manager to insert vectors into Milvus while ensuring
            data is flushed.

            For more information about Milvus:
                - https://github.com/milvus-io/milvus/
        """

        def __init__(self, client: 'Milvus', collection_name: str):
            self.logger = get_logger(self.__class__.__name__)
            self.client = client
            self.collection_name = collection_name

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.logger.info(f'Seding flush command to Milvus Server for collection: {self.collection_name}')
            self.client.flush([self.collection_name])

        def insert(self, keys: list, vectors: 'np.ndarray'):
            status, _ = self.client.insert(collection_name=self.collection_name, records=vectors, ids=keys)
            if not status.OK():
                self.logger.error('Insert failed: {}'.format(status))
                raise MilvusDBException(status.message)

    def __init__(self, host: str, port: int, collection_name: str):
        """
        Initialize an MilvusDBHandler

        :param host: Host of the Milvus Server
        :param port: Port to connect to the Milvus Server
        :param collection_name: Name of the collection where the Handler will insert and query vectors.
        """
        self.logger = get_logger(self.__class__.__name__)
        self.host = host
        self.port = str(port)
        self.collection_name = collection_name
        self.milvus_client = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        if self.milvus_client is None or not self.milvus_client.server_status()[0].OK():
            self.logger.info(f'Setting connection to Milvus Server at {self.host}:{self.port}')
            self.milvus_client = Milvus(self.host, self.port)
        return self

    def close(self):
        self.logger.info(f'Closing connection to Milvus Server at {self.host}:{self.port}')
        self.milvus_client.close()

    def insert(self, keys: 'np.ndarray', vectors: 'np.ndarray'):
        with MilvusDBHandler.MilvusDBInserter(self.milvus_client, self.collection_name) as db:
            db.insert(reduce(operator.concat, keys.tolist()), vectors)

    def build_index(self, index_type: str, index_params: dict):
        type = IndexType.FLAT
        if index_type in MilvusDBHandler.index_types_map.keys():
            type = MilvusDBHandler.index_types_map[index_type]

        self.logger.info(f'Creating index of type: {index_type} at'
                         f' Milvus Server. collection: {self.collection_name} with index params: {index_params}')
        status = self.milvus_client.create_index(self.collection_name, type, index_params)
        if not status.OK():
            self.logger.error('Creating index failed: {}'.format(status))
            raise MilvusDBException(status.message)

    def search(self, query_vectors: 'np.ndarray', top_k: int, search_params: dict = None):
        self.logger.info(f'Querying collection: {self.collection_name} with search params: {search_params}')
        status, results = self.milvus_client.search(collection_name=self.collection_name,
                                                    query_records=query_vectors, top_k=top_k, params=search_params)
        if not status.OK():
            self.logger.error('Querying index failed: {}'.format(status))
            raise MilvusDBException(status.message)
        else:
            return results.distance_array, results.id_array
