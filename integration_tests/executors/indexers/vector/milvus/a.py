import os
import shutil
import time
import numpy as np

from jina.executors.indexers.vector.milvusdb.milvusdbhandler import MilvusDBHandler
from milvus import Milvus, IndexType, MetricType, Status

from integration_tests import JinaTestCase

#cur_dir = os.path.dirname(os.path.abspath(__file__))
# TODO: Generate random
port = 19530
_HOST = '127.0.0.1'
_PORT = '19530'  # default value
# _PORT = '19121'  # default http
host = '127.0.0.1'
img_name = 'milvusdb/milvusdb:0.10.0-cpu-d061620-5f3c00'
collection_name = 'example_collection_'


def create_collection():
    print("CREATE COLLECTION")
    client = Milvus(_HOST, _PORT)
    print("CREATED COLLECTION")

    status, ok = client.has_collection(collection_name)
    if not ok:
        param = {
            'collection_name': collection_name,
            'dimension': 3
        }
        client.create_collection(param)
    client.close()