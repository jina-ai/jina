import os
import unittest

import numpy as np

from jina.drivers.helper import array2blob
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

    def test_doc_iters(self):
        a = random_docs(10, 5)
        for d in a:
            print(d)

    def test_simple_route(self):
        f = Flow().add(driver_group='route')
        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True, callback=print)

    def test_index(self):
        f = Flow().add(exec_yaml_path='yaml/test-index.yml',
                       driver_group='index-chunk', replicas=3, separated_workspace=True)
        with f.build(copy_flow=True) as fl:
            fl.index(raw_bytes=random_docs(1000), in_proto=True)

        for j in range(3):
            self.assertTrue(os.path.exists('test2-%d/test2.bin' % j))
            self.assertTrue(os.path.exists('test2-%d/tmp2' % j))
            self.add_tmpfile('test2-%d/test2.bin' % j, 'test2-%d/tmp2' % j, 'test2-%d' % j)

    def test_query(self):
        f = Flow().add(exec_yaml_path='yaml/test-query.yml',
                       driver_group='index-chunk', replicas=3, separated_workspace=True)
        with f.build(copy_flow=True) as fl:
            fl.search(raw_bytes=random_docs(1), in_proto=True, callback=get_result, top_k=100)


if __name__ == '__main__':
    unittest.main()
