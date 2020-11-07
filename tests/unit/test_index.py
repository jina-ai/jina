import os
import multiprocessing as mp

import pytest
import numpy as np


from jina.flow import Flow
from jina.proto import jina_pb2
from jina.parser import set_flow_parser
from jina.enums import FlowOptimizeLevel
from jina.executors.indexers.vector import NumpyIndexer
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


def get_result(resp):
    n = []
    for d in resp.search.docs:
        n.append([k.id for k in d.matches])
    n = np.array(n)
    # each doc should return a list of top-100
    np.testing.assert_equal(n.shape[0], 2)
    np.testing.assert_equal(n.shape[1], 50)


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


def test_doc_iters():
    docs = random_docs(3, 5)
    for doc in docs:
        assert isinstance(doc, jina_pb2.Document)

def test_simple_route():
    f = Flow().add(uses='_pass')
    with f:
        f.index(input_fn=random_docs(10))

def test_update_method(test_metas):
    with DummyIndexer(index_filename='testa.bin', metas=test_metas) as indexer:
        indexer.save()
        assert not os.path.exists(indexer.save_abspath)
        assert not os.path.exists(indexer.index_abspath)
        indexer.add()
        indexer.save()
        assert os.path.exists(indexer.save_abspath)
        assert os.path.exists(indexer.index_abspath)

    with DummyIndexer2(index_filename='testb.bin', metas=test_metas) as indexer:
        indexer.save()
        assert not os.path.exists(indexer.save_abspath)
        assert not os.path.exists(indexer.index_abspath)
        indexer.add(np.array([1, 2, 3]), np.array([[1, 1, 1], [2, 2, 2]]))
        indexer.save()
        assert os.path.exists(indexer.save_abspath)
        assert os.path.exists(indexer.index_abspath)


@pytest.mark.skipif('GITHUB_WORKFLOW' in os.environ, reason='skip the network test on github workflow')
def test_two_client_route_parallel():
    fa1 = set_flow_parser().parse_args(['--optimize-level', str(FlowOptimizeLevel.NONE)])
    f1 = Flow(fa1).add(uses='_pass', parallel=3)
    f2 = Flow(optimize_level=FlowOptimizeLevel.IGNORE_GATEWAY).add(uses='_pass', parallel=3)

    def start_client(fl):
        fl.index(input_fn=random_docs(10))

    with f1:
        assert f1.num_peas == 6
        t1 = mp.Process(target=start_client, args=(f1,))
        t1.daemon = True
        t2 = mp.Process(target=start_client, args=(f1,))
        t2.daemon = True

        t1.start()
        t2.start()

    with f2:
        # no optimization can be made because we ignored the gateway
        assert f2.num_peas == 6
        t1 = mp.Process(target=start_client, args=(f2,))
        t1.daemon = True
        t2 = mp.Process(target=start_client, args=(f2,))
        t2.daemon = True

        t1.start()
        t2.start()


@pytest.mark.skipif('GITHUB_WORKFLOW' in os.environ, reason='skip the network test on github workflow')
def test_two_client_route():
    def start_client(fl):
        fl.index(input_fn=random_docs(10))

    with Flow().add(uses='_pass') as f:
        t1 = mp.Process(target=start_client, args=(f,))
        t1.daemon = True
        t2 = mp.Process(target=start_client, args=(f,))
        t2.daemon = True

        t1.start()
        t2.start()


def test_index():
    f = Flow().add(uses=os.path.join(cur_dir, 'yaml/test-index.yml'), parallel=3, separated_workspace=True)
    with f:
        f.index(input_fn=random_docs(1000))

    for j in range(3):
        assert os.path.exists(f'test2-{j + 1}/test2.bin')
        assert os.path.exists(f'test2-{j + 1}/tmp2')

    with f:
        f.search(input_fn=random_docs(2), output_fn=get_result, top_k=50)


def test_chunk_joint_idx():
    def validate(req, indexer_name):
        assert req.status.code < jina_pb2.Status.ERROR
        assert req.search.docs[0].matches[0].score.op_name == indexer_name

    with Flow().add(uses=os.path.join(cur_dir, 'yaml/test-joint.yml')) as f:
        f.index(random_docs(100, chunks_per_doc=0))

    with Flow().add(uses=os.path.join(cur_dir, 'yaml/test-joint.yml')) as g:
        g.search(random_docs(10, chunks_per_doc=0), output_fn=lambda x: validate(x, 'NumpyIndexer'))
