import os

import pytest
import numpy as np

from jina.executors.indexers.vector import NumpyIndexer
from jina.flow import Flow
from jina.proto import jina_pb2
from jina import Document
from tests import random_docs, validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def test_workspace_index(tmpdir):
    os.environ['JINA_TEST_INDEX'] = str(tmpdir)
    workspace_path = os.environ['JINA_TEST_INDEX']
    yield workspace_path
    del os.environ['JINA_TEST_INDEX']


@pytest.fixture(scope='function')
def test_workspace_joint(tmpdir):
    os.environ['JINA_TEST_JOINT'] = str(tmpdir)
    workspace_path = os.environ['JINA_TEST_JOINT']
    yield workspace_path
    del os.environ['JINA_TEST_JOINT']


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
            raise ValueError(
                f'vectors shape {vectors.shape} is not valid, expecting "vectors" to have rank of 2'
            )

        if not self.num_dim:
            self.num_dim = vectors.shape[1]
            self.dtype = vectors.dtype.name
        elif self.num_dim != vectors.shape[1]:
            raise ValueError(
                "vectors' shape [%d, %d] does not match with indexers's dim: %d"
                % (vectors.shape[0], vectors.shape[1], self.num_dim)
            )
        elif self.dtype != vectors.dtype.name:
            raise TypeError(
                f"vectors' dtype {vectors.dtype.name} does not match with indexers's dtype: {self.dtype}"
            )
        elif keys.shape[0] != vectors.shape[0]:
            raise ValueError(
                'number of key %d not equal to number of vectors %d'
                % (keys.shape[0], vectors.shape[0])
            )
        elif self.key_dtype != keys.dtype.name:
            raise TypeError(
                f"keys' dtype {keys.dtype.name} does not match with indexers keys's dtype: {self.key_dtype}"
            )

        self.write_handler.write(vectors.tobytes())
        self.key_bytes += keys.tobytes()
        self.key_dtype = keys.dtype.name
        self._size += keys.shape[0]


def test_doc_iters():
    docs = random_docs(3, 5)
    for doc in docs:
        assert isinstance(doc, Document)


def test_simple_route():
    f = Flow().add()
    with f:
        f.index(inputs=random_docs(10))


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


def test_index(test_workspace_index):
    f = Flow().add(uses=os.path.join(cur_dir, 'yaml/test-index.yml'), parallel=3)
    with f:
        f.index(inputs=random_docs(50))
    for j in range(3):
        assert os.path.exists(os.path.join(test_workspace_index, f'test2-{j + 1}/tmp2'))


def test_compound_idx(test_workspace_joint, mocker):
    def validate(req):
        assert req.status.code < jina_pb2.StatusProto.ERROR
        assert req.search.docs[0].matches[0].score.op_name == 'NumpyIndexer'

    with Flow().add(uses=os.path.join(cur_dir, 'yaml/test-joint.yml')) as f:
        f.index(random_docs(100, chunks_per_doc=0))

    response_mock = mocker.Mock()
    with Flow().add(uses=os.path.join(cur_dir, 'yaml/test-joint.yml')) as g:
        g.search(random_docs(10, chunks_per_doc=0), on_done=response_mock)

    validate_callback(response_mock, validate)
