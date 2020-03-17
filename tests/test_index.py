import multiprocessing as mp
import os
import time
import unittest

import numpy as np

from jina.drivers.helper import array2blob
from jina.enums import FlowOptimizeLevel
from jina.flow import Flow
from jina.proto import jina_pb2
from tests import JinaTestCase


def random_docs(num_docs, chunks_per_doc=5, embed_dim=10):
    c_id = 0
    for j in range(num_docs):
        d = jina_pb2.Document()
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            c.embedding.CopyFrom(array2blob(np.random.random([embed_dim])))
            c.chunk_id = c_id
            c.doc_id = j
            c_id += 1
        yield d


def get_result(resp):
    n = []
    for d in resp.search.docs:
        for c in d.chunks:
            n.append([k.match_chunk.chunk_id for k in c.topk_results])
    n = np.array(n)
    # each chunk should return a list of top-100
    np.testing.assert_equal(n.shape[0], 5)
    np.testing.assert_equal(n.shape[1], 100)


class MyTestCase(JinaTestCase):

    def tearDown(self) -> None:
        time.sleep(2)
        super().tearDown()

    def test_doc_iters(self):
        a = random_docs(3, 5)
        for d in a:
            print(d)

    def test_simple_route(self):
        f = Flow().add(yaml_path='route')
        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)

    @unittest.skipIf(os.getenv('GITHUB_WORKFLOW', False), 'skip the network test on github workflow')
    def test_two_client_route_replicas(self):
        f1 = Flow(optimize_level=FlowOptimizeLevel.NONE).add(yaml_path='route', replicas=3)
        f2 = Flow(optimize_level=FlowOptimizeLevel.IGNORE_GATEWAY).add(yaml_path='route', replicas=3)
        f3 = Flow(optimize_level=FlowOptimizeLevel.FULL).add(yaml_path='route', replicas=3)

        def start_client(fl):
            fl.index(raw_bytes=random_docs(10), in_proto=True)

        with f1.build() as fl1:
            self.assertEqual(fl1.num_peas, 6)
            t1 = mp.Process(target=start_client, args=(fl1,))
            t1.daemon = True
            t2 = mp.Process(target=start_client, args=(fl1,))
            t2.daemon = True

            t1.start()
            t2.start()
            time.sleep(5)

        with f2.build() as fl2:
            self.assertEqual(fl2.num_peas, 6)
            t1 = mp.Process(target=start_client, args=(fl2,))
            t1.daemon = True
            t2 = mp.Process(target=start_client, args=(fl2,))
            t2.daemon = True

            t1.start()
            t2.start()
            time.sleep(5)

        with f3.build() as fl3:
            self.assertEqual(fl3.num_peas, 4)

    @unittest.skipIf(os.getenv('GITHUB_WORKFLOW', False), 'skip the network test on github workflow')
    def test_two_client_route(self):
        f = Flow().add(yaml_path='route')

        def start_client(fl):
            fl.index(raw_bytes=random_docs(10), in_proto=True)

        with f.build() as fl:
            t1 = mp.Process(target=start_client, args=(fl,))
            t1.daemon = True
            t2 = mp.Process(target=start_client, args=(fl,))
            t2.daemon = True

            t1.start()
            t2.start()
            time.sleep(5)

    def test_index(self):
        f = Flow().add(yaml_path='yaml/test-index.yml', replicas=3, separated_workspace=True)
        with f.build(copy_flow=True) as fl:
            fl.index(raw_bytes=random_docs(1000), in_proto=True)

        for j in range(3):
            self.assertTrue(os.path.exists('test2-%d/test2.bin' % j))
            self.assertTrue(os.path.exists('test2-%d/tmp2' % j))
            self.add_tmpfile('test2-%d/test2.bin' % j, 'test2-%d/tmp2' % j, 'test2-%d' % j)

        time.sleep(3)
        with f.build(copy_flow=True) as fl:
            fl.search(raw_bytes=random_docs(1), in_proto=True, callback=get_result, top_k=100)


if __name__ == '__main__':
    unittest.main()
