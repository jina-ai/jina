import numpy as np
import pytest
from scipy.sparse import coo_matrix

from jina.ndarray.dense.numpy import DenseNdArray
from jina.ndarray.sparse.scipy import SparseNdArray


@pytest.mark.parametrize('sp_format', ['coo', 'bsr', 'csc', 'csr'])
def test_scipy_sparse(sp_format):
    row = np.array([0, 3, 1, 0])
    col = np.array([0, 3, 1, 2])
    data = np.array([4, 5, 7, 9])
    a = coo_matrix((data, (row, col)), shape=(4, 4))
    dense_a = a.toarray()
    b = SparseNdArray(sp_format=sp_format)
    # write to proto
    b.value = a
    # read from proto
    dense_b = b.value.toarray()
    np.testing.assert_equal(dense_b, dense_a)


@pytest.mark.parametrize('dtype', ['float64', 'float32', 'float16',
                                   'int64', 'int32', 'int16',
                                   'uint32', 'uint8'])
def test_numpy_dense(dtype):
    a = (100 * np.random.random([10, 6, 8, 2])).astype(dtype)
    b = DenseNdArray()
    # set
    b.value = a
    # get
    np.testing.assert_equal(b.value.shape, a.shape)
    np.testing.assert_equal(b.value, a)
