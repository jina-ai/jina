import numpy as np
import pytest

from jina.proto.ndarray.dense.numpy import DenseNdArray


def test_empty_ndarray():
    a = DenseNdArray()
    assert a.value is None

    from jina.proto.ndarray.sparse.pytorch import SparseNdArray as sp1
    a = sp1()
    assert a.value is None

    from jina.proto.ndarray.sparse.scipy import SparseNdArray as sp2
    a = sp2()
    assert a.value is None

    from jina.proto.ndarray.sparse.tensorflow import SparseNdArray as sp2
    a = sp2()
    assert a.value is None

    from jina.proto.ndarray.sparse.numpy import SparseNdArray as sp2
    a = sp2()
    assert a.value is None

    from jina.proto.ndarray.generic import GenericNdArray as sp2
    a = sp2()
    assert a.value is None


@pytest.mark.parametrize('sp_format', ['coo'])
def test_scipy_sparse(sp_format):
    from scipy.sparse import coo_matrix
    from jina.proto.ndarray.sparse.scipy import SparseNdArray
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


@pytest.mark.parametrize('idx_shape', [([[0], [1], [2]], [3]),
                                       ([[0, 1], [0, 2], [1, 2]], [3, 3]),
                                       ([[0, 1, 1], [0, 1, 2], [2, 1, 2]], [3, 3, 3])])
def test_tf_sparse(idx_shape):
    import tensorflow as tf
    from tensorflow import SparseTensor
    from jina.proto.ndarray.sparse.tensorflow import SparseNdArray
    a = SparseTensor(indices=idx_shape[0], values=[1, 2, 3], dense_shape=idx_shape[1])
    b = SparseNdArray()
    b.value = a
    np.testing.assert_equal(tf.sparse.to_dense(b.value).numpy(), tf.sparse.to_dense(a).numpy())


@pytest.mark.parametrize('idx_shape', [([[0], [1], [2]], [3]),
                                       ([[0, 2], [1, 0], [1, 2]], [2, 3]),
                                       ([[0, 1, 1], [0, 1, 2], [2, 1, 2]], [3, 3, 3])])
def test_torch_sparse_with_transpose(idx_shape, transpose=True):
    from jina.proto.ndarray.sparse.pytorch import SparseNdArray
    import torch
    i = torch.LongTensor(idx_shape[0])
    v = torch.FloatTensor([3, 4, 5])
    a = torch.sparse.FloatTensor(i.t() if transpose else i, v, torch.Size(idx_shape[1]))

    b = SparseNdArray(transpose_indices=transpose)
    b.value = a
    np.testing.assert_equal(b.value.to_dense().numpy(), a.to_dense().numpy())


@pytest.mark.parametrize('idx_shape', [([[0, 1, 2]], [3]),
                                       ([[0, 2, 1], [1, 0, 2]], [3, 3]),
                                       ([[0, 1, 1], [0, 1, 2], [2, 1, 2]], [3, 3, 3])])
def test_torch_sparse(idx_shape, transpose=False):
    from jina.proto.ndarray.sparse.pytorch import SparseNdArray
    import torch
    i = torch.LongTensor(idx_shape[0])
    v = torch.FloatTensor([3, 4, 5])
    a = torch.sparse.FloatTensor(i, v, torch.Size(idx_shape[1]))

    b = SparseNdArray(transpose_indices=transpose)
    b.value = a
    np.testing.assert_equal(b.value.to_dense().numpy(), a.to_dense().numpy())


def test_generic():
    from jina.proto.ndarray.generic import GenericNdArray
    from scipy.sparse import coo_matrix

    row = np.array([0, 3, 1, 0])
    col = np.array([0, 3, 1, 2])
    data = np.array([4, 5, 7, 9])
    a = coo_matrix((data, (row, col)), shape=(4, 4))
    dense_a = a.toarray()

    b = GenericNdArray(is_sparse=True)

    b.value = a

    dense_b = b.value.toarray()
    np.testing.assert_equal(dense_b, dense_a)

    c = np.random.random([10, 3, 4])

    # without change of `is_sparse`, this should raise error
    with pytest.raises(AttributeError):
        b.value = c
    b.is_sparse = False
    b.value = c

    np.testing.assert_equal(b.value, c)


@pytest.mark.parametrize('shape', [[10], [7, 8], [7, 8, 9]])
def test_dummy_numpy_sparse(shape):
    a = np.random.random(shape)
    a[a > 0.5] = 1

    from jina.proto.ndarray.sparse.numpy import SparseNdArray
    b = SparseNdArray()
    b.value = a

    np.testing.assert_almost_equal(a, b.value)
