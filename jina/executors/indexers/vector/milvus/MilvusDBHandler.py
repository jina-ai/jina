import numpy as np
from milvus import Milvus, IndexType, MetricType, Status


# TODO: Handle exceptions and logging

class MilvusDBHandler:
    class MilvusDBInserter:
        def __init__(self, client: 'Milvus', collection_name: str):
            self.client = client
            self.collection_name = collection_name

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.client.flush([self.collection_name])

        def insert(self, keys: 'np.ndarray', vectors: 'np.ndarray'):
            status, _ = self.client.insert(collection_name=self.collection_name, records=vectors, ids=keys)
            if not status.OK():
                # TODO: Should I raise?
                print('Insert failed: {}'.format(status))

    def __init__(self, host: str, port: int, collection_name: str):
        self.host = host
        self.port = str(port)
        self.collection_name = collection_name
        self.milvus_client = None
        pass

    def __enter__(self):
        self.milvus_client = Milvus(self.host, self.port)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.milvus_client.close()
        pass

    def insert(self, keys: 'np.ndarray', vectors: 'np.ndarray'):
        with MilvusDBHandler.MilvusDBInserter(self.milvus_client, self.collection_name) as db:
            db.insert(keys, vectors)

    def build_index(self, index_type: 'IndexType', index_params: dict):
        status = self.milvus_client.create_index(self.collection_name, index_type, index_params)
        if not status.OK():
            # TODO: Should I raise?
            print('Creating index failed: {}'.format(status))

    def search(self, query_vectors: 'np.ndarray', top_k: int, search_params: dict):
        status, results = self.milvus_client.search(collection_name=self.collection_name,
                                                    query_records=query_vectors, top_k=top_k, params=search_params)
        if not status.OK():
            # TODO: Should I raise?
            print('Querying index failed: {}'.format(status))
            return None
        else:
            return results

