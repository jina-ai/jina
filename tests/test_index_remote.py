import multiprocessing as mp
import os
import time
import unittest

import numpy as np

from jina.drivers.helper import array2blob
from jina.enums import FlowOptimizeLevel
from jina.executors.indexers.numpy import NumpyIndexer
from jina.flow import Flow
from jina.main.parser import set_gateway_parser
from jina.peapods.pod import GatewayPod
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


class DummyIndexer(NumpyIndexer):
    # the add() function is simply copied from NumpyIndexer
    def add(self, *args, **kwargs):
        pass


class DummyIndexer2(NumpyIndexer):
    # the add() function is simply copied from NumpyIndexer
    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        if len(vectors.shape) != 2:
            raise ValueError('vectors shape %s is not valid, expecting "vectors" to have rank of 2' % vectors.shape)

        if not self.num_dim:
            self.num_dim = vectors.shape[1]
            self.dtype = vectors.dtype.name
        elif self.num_dim != vectors.shape[1]:
            raise ValueError(
                "vectors' shape [%d, %d] does not match with indexers's dim: %d" %
                (vectors.shape[0], vectors.shape[1], self.num_dim))
        elif self.dtype != vectors.dtype.name:
            raise TypeError(
                "vectors' dtype %s does not match with indexers's dtype: %s" %
                (vectors.dtype.name, self.dtype))
        elif keys.shape[0] != vectors.shape[0]:
            raise ValueError('number of key %d not equal to number of vectors %d' % (keys.shape[0], vectors.shape[0]))
        elif self.key_dtype != keys.dtype.name:
            raise TypeError(
                "keys' dtype %s does not match with indexers keys's dtype: %s" %
                (keys.dtype.name, self.key_dtype))

        self.write_handler.write(vectors.tobytes())
        self.key_bytes += keys.tobytes()
        self.key_dtype = keys.dtype.name
        self._size += keys.shape[0]


@unittest.skipIf('GITHUB_WORKFLOW' in os.environ, 'skip the network test on github workflow')
class MyTestCase(JinaTestCase):

    def tearDown(self) -> None:
        super().tearDown()
        time.sleep(2)

    def test_index_remote(self):
        f_args = set_gateway_parser().parse_args(['--allow_spawn'])

        def start_gateway():
            with GatewayPod(f_args):
                time.sleep(20)

        t = mp.Process(target=start_gateway)
        t.daemon = True
        t.start()

        f = Flow().add(yaml_path='yaml/test-index.yml',
                       replicas=3, separated_workspace=True,
                       host='localhost', port_grpc=f_args.port_grpc)

        with f.build(copy_flow=True) as fl:
            fl.index(raw_bytes=random_docs(1000), in_proto=True)

        time.sleep(3)
        for j in range(3):
            self.assertTrue(os.path.exists('test2-%d/test2.bin' % j))
            self.assertTrue(os.path.exists('test2-%d/tmp2' % j))
            self.add_tmpfile('test2-%d/test2.bin' % j, 'test2-%d/tmp2' % j, 'test2-%d' % j)

    def test_index_remote_rpi(self):
        f_args = set_gateway_parser().parse_args(['--allow_spawn'])

        def start_gateway():
            with GatewayPod(f_args):
                time.sleep(50)

        t = mp.Process(target=start_gateway)
        t.daemon = True
        t.start()

        f = (Flow(optimize_level=FlowOptimizeLevel.IGNORE_GATEWAY)
             .add(yaml_path='yaml/test-index.yml',
                  replicas=3, separated_workspace=True,
                  host='192.168.31.76', port_grpc=44444))

        with f.build(copy_flow=True) as fl:
            fl.index(raw_bytes=random_docs(1000), in_proto=True)


if __name__ == '__main__':
    unittest.main()
