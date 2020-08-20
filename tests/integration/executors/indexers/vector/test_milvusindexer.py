import os
import shutil
import time

import numpy as np
from jina.hub.indexers.vector.MilvusIndexer import MilvusIndexer
from jina.hub.indexers.vector.MilvusIndexer.MilvusDBHandler import MilvusDBHandler
from milvus import Milvus
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))

port = 19530
host = '127.0.0.1'
img_name = 'milvusdb/milvus:0.10.0-cpu-d061620-5f3c00'


def create_collection(collection_name):
    client = Milvus(host, str(port))

    status, ok = client.has_collection(collection_name)
    if not ok:
        param = {
            'collection_name': collection_name,
            'dimension': 3,
        }
        client.create_collection(param)
    client.close()


class MilvusIndexerTestCase(JinaTestCase):
    def docker_run(self):
        import docker
        host_milvus_tmp = os.path.join(cur_dir, 'milvus_tmp')
        conf_tmp = os.path.join(host_milvus_tmp, 'conf')
        os.makedirs(host_milvus_tmp, exist_ok=True)
        os.makedirs(conf_tmp, exist_ok=True)
        shutil.copy(os.path.join(cur_dir, 'server_config.yaml'), conf_tmp)
        self.add_tmpfile(host_milvus_tmp)
        client = docker.from_env()
        client.images.pull(img_name)

        bind_volumes = {
            os.path.join(host_milvus_tmp, 'db'): {'bind': '/var/lib/milvusdb/db', 'mode': 'rw'},
            os.path.join(host_milvus_tmp, 'conf'): {'bind': '/var/lib/milvusdb/conf', 'mode': 'rw'},
            os.path.join(host_milvus_tmp, 'logs'): {'bind': '/var/lib/milvusdb/logs', 'mode': 'rw'},
            os.path.join(host_milvus_tmp, 'wal'): {'bind': '/var/lib/milvusdb/wal', 'mode': 'rw'}
        }

        self.container = client.containers.run(img_name, name='milvus_test_image',
                                               volumes=bind_volumes, detach=True, auto_remove=True,
                                               ports={f'{port}/tcp': f'{port}', '19121/tcp': '19121'},
                                               network_mode='host')

        client.close()

    def docker_clean(self):
        self.container.stop()

    def tearDown(self) -> None:
        self.docker_clean()
        super().tearDown()
        time.sleep(2)

    def setUp(self) -> None:
        super().setUp()
        self.docker_run()

    def test_milvusdbhandler_simple(self):
        collection_name = 'simple_milvus'
        create_collection(collection_name)

        vectors = np.array([[1, 1, 1],
                            [10, 10, 10],
                            [100, 100, 100],
                            [1000, 1000, 1000]])
        keys = np.array([0, 1, 2, 3]).reshape(-1, 1)
        with MilvusDBHandler(host, port, collection_name) as db:
            db.insert(keys, vectors)
            dist, idx = db.search(vectors, 2)
            dist = np.array(dist)
            idx = np.array(idx)
            assert idx.shape == dist.shape
            assert idx.shape == (4, 2)
            np.testing.assert_equal(idx, np.array([[0, 1], [1, 0], [2, 1], [3, 2]]))

    def test_milvusdbhandler_build(self):
        collection_name = 'build_milvus'
        create_collection(collection_name)

        vectors = np.array([[1, 1, 1],
                            [10, 10, 10],
                            [100, 100, 100],
                            [1000, 1000, 1000]])
        keys = np.array([0, 1, 2, 3]).reshape(-1, 1)
        with MilvusDBHandler(host, port, collection_name) as db:
            db.insert(keys, vectors)
            db.build_index(index_type='IVF,Flat', index_params={'nlist': 2})

            dist, idx = db.search(vectors, 2, {'nprobe': 2})
            dist = np.array(dist)
            idx = np.array(idx)
            assert idx.shape == dist.shape
            assert idx.shape == (4, 2)
            np.testing.assert_equal(idx, np.array([[0, 1], [1, 0], [2, 1], [3, 2]]))

    def test_milvus_indexer(self):
        collection_name = 'milvus_indexer'
        create_collection(collection_name)

        vectors = np.array([[1, 1, 1],
                            [10, 10, 10],
                            [100, 100, 100],
                            [1000, 1000, 1000]])
        keys = np.array([0, 1, 2, 3]).reshape(-1, 1)
        with MilvusIndexer(host=host, port=port,
                           collection_name=collection_name, index_type='IVF,Flat',
                           index_params={'nlist': 2}) as indexer:
            indexer.add(keys, vectors)
            idx, dist = indexer.query(vectors, 2, search_params={'nprobe': 2})
            dist = np.array(dist)
            idx = np.array(idx)
            assert idx.shape == dist.shape
            assert idx.shape == (4, 2)
            np.testing.assert_equal(idx, np.array([[0, 1], [1, 0], [2, 1], [3, 2]]))
