import os
import time
import multiprocessing as mp

import pytest
import numpy as np

from jina.flow import Flow
from jina.helper import random_port
from jina.peapods.pod import GatewayPod
from jina.enums import FlowOptimizeLevel
from jina.parser import set_gateway_parser
from jina.executors.indexers.vector import NumpyIndexer
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


def get_result(resp):
    n = []
    for d in resp.search.docs:
        for c in d.chunks:
            n.append([k.id for k in c.matches])
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
            raise ValueError(f'vectors shape {vectors.shape} is not valid, expecting "vectors" to have rank of 2')

        if not self.num_dim:
            self.num_dim = vectors.shape[1]
            self.dtype = vectors.dtype.name
        elif self.num_dim != vectors.shape[1]:
            raise ValueError(
                "vectors' shape [%d, %d] does not match with indexers's dim: %d" %
                (vectors.shape[0], vectors.shape[1], self.num_dim))
        elif self.dtype != vectors.dtype.name:
            raise TypeError(
                f"vectors' dtype {vectors.dtype.name} does not match with indexers's dtype: {self.dtype}")
        elif keys.shape[0] != vectors.shape[0]:
            raise ValueError('number of key %d not equal to number of vectors %d' % (keys.shape[0], vectors.shape[0]))
        elif self.key_dtype != keys.dtype.name:
            raise TypeError(
                f"keys' dtype {keys.dtype.name} does not match with indexers keys's dtype: {self.key_dtype}")

        self.write_handler.write(vectors.tobytes())
        self.key_bytes += keys.tobytes()
        self.key_dtype = keys.dtype.name
        self._size += keys.shape[0]


@pytest.fixture(scope='function')
def test_workspace(tmpdir):
    os.environ['JINA_TEST_INDEX_REMOTE'] = str(tmpdir)
    workspace_path = os.environ['JINA_TEST_INDEX_REMOTE']
    yield workspace_path
    del os.environ['JINA_TEST_INDEX_REMOTE']


@pytest.mark.skipif('GITHUB_WORKFLOW' in os.environ, reason='skip the network test on github workflow')
def test_index_remote(test_workspace):
    f_args = set_gateway_parser().parse_args(['--host', '0.0.0.0'])

    def start_gateway():
        with GatewayPod(f_args):
            time.sleep(20)

    t = mp.Process(target=start_gateway)
    t.daemon = True
    t.start()

    f = Flow().add(
        uses=os.path.join(cur_dir, 'yaml/test-index-remote.yml'),
        parallel=3,
        separated_workspace=True,
        host='0.0.0.0',
        port_expose=f_args.port_expose
    )

    with f:
        f.index(input_fn=random_docs(1000))

    time.sleep(3)
    for j in range(3):
        bin_path = os.path.join(test_workspace, f'test2-{j + 1}/test2.bin')
        index_filename_path = os.path.join(test_workspace, f'test2-{j + 1}/tmp2')
        assert os.path.exists(bin_path)
        assert os.path.exists(index_filename_path)


@pytest.mark.skipif('GITHUB_WORKFLOW' in os.environ, reason='skip the network test on github workflow')
def test_index_remote_rpi(test_workspace):
    f_args = set_gateway_parser().parse_args(['--host', '0.0.0.0'])

    def start_gateway():
        with GatewayPod(f_args):
            time.sleep(3)

    t = mp.Process(target=start_gateway)
    t.daemon = True
    t.start()

    f = Flow(optimize_level=FlowOptimizeLevel.IGNORE_GATEWAY).add(
        uses=os.path.join(cur_dir, 'yaml/test-index-remote.yml'),
        parallel=3,
        separated_workspace=True,
        host='0.0.0.0',
        port_expose=random_port())

    with f:
        f.index(input_fn=random_docs(1000))
