import pytest
import numpy as np

from jina.proto import jina_pb2
from jina.types.ndarray.generic import NdArray
from jina.types.ndarray.dense.numpy import DenseNdArray
from jina.types.ndarray.sparse.tensorflow import SparseNdArray as TFSparseNdArray
from jina.types.ndarray.sparse.pytorch import SparseNdArray as PTSparseNdArray
from jina.types.ndarray.sparse.scipy import SparseNdArray as SPSparseNdArray


@pytest.fixture
def tf_sparse_tensor():
    from tensorflow import SparseTensor

    return SparseTensor(indices=[[0, 0], [1, 2]], values=[1, 2], dense_shape=[3, 4])


@pytest.fixture
def pt_sparse_tensor():
    import torch

    i = [[0, 2], [1, 0], [1, 2]]
    v = [3, 4, 5]
    return torch.sparse_coo_tensor(list(zip(*i)), v, (2, 3))


@pytest.fixture
def sp_sparse_tensor():
    from scipy.sparse import csr_matrix

    row = np.array([0, 0, 1, 2, 2, 2])
    col = np.array([0, 2, 2, 0, 1, 2])
    data = np.array([1, 2, 3, 4, 5, 6])
    return csr_matrix((data, (row, col)), shape=(3, 3))


@pytest.fixture
def np_dense_tensor(sp_sparse_tensor):
    return sp_sparse_tensor.todense()


def tf_ndarray():
    return NdArray(None, True, None, TFSparseNdArray)


def sp_ndarray():
    return NdArray(None, True, None, SPSparseNdArray)


def pt_ndarray():
    return NdArray(None, True, None, PTSparseNdArray)


def np_ndarray():
    return NdArray(None, False, DenseNdArray, None)


@pytest.fixture(
    params=[
        tf_ndarray,
        sp_ndarray,
        pt_ndarray,
        np_ndarray,
    ]
)
def NdArrayCls(request):
    yield request.param


def test_null_proto(NdArrayCls):
    assert NdArrayCls().null_proto() == jina_pb2.NdArrayProto()


def test_value_get_set(
    NdArrayCls, tf_sparse_tensor, pt_sparse_tensor, sp_sparse_tensor, np_dense_tensor
):
    ndarray = NdArrayCls()
    assert ndarray.value is None
    if isinstance(ndarray, TFSparseNdArray):
        ndarray.value = tf_sparse_tensor
        assert ndarray.value == tf_sparse_tensor
        assert ndarray.is_sparse is True
    elif isinstance(ndarray, SPSparseNdArray):
        ndarray.value = sp_sparse_tensor
        assert ndarray.value == sp_sparse_tensor
        assert ndarray.is_sparse is True
    elif isinstance(ndarray, PTSparseNdArray):
        ndarray.value = pt_sparse_tensor
        assert ndarray.value == pt_sparse_tensor
        assert ndarray.is_sparse is True
    elif isinstance(ndarray, DenseNdArray):
        ndarray.value = np_dense_tensor
        assert ndarray.value == np_dense_tensor
        assert ndarray.is_sparse is False
