import numpy as np
import pytest

from jina.ndarray.dense.numpy import DenseNdArray


@pytest.mark.parametrize('sp_format', ['coo', 'bsr', 'csc', 'csr'])
def test_scipy_sparse(sp_format):
    from scipy.sparse import coo_matrix
    from jina.ndarray.sparse.scipy import SparseNdArray
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


@pytest.mark.parametrize('idx_shape', [([[0, 1, 1]], [3]),
                                       ([[0, 1, 1], [2, 0, 2]], [2, 3]),
                                       ([[0, 1, 1], [2, 0, 2], [1, 0, 2]], [2, 3, 3])])
def test_tf_sparse(idx_shape):
    import tensorflow as tf
    from tensorflow import SparseTensor
    from jina.ndarray.sparse.tensorflow import SparseNdArray
    a = SparseTensor(indices=idx_shape[0], values=[1, 2], dense_shape=idx_shape[1])
    b = SparseNdArray()
    b.value = a
    np.testing.assert_equal(tf.sparse.to_dense(b.value).numpy(), tf.sparse.to_dense(a).numpy())


@pytest.mark.parametrize('idx_shape', [([[0, 1, 1]], [3]),
                                       ([[0, 1, 1], [2, 0, 2]], [2, 3]),
                                       ([[0, 1, 1], [2, 0, 2], [1, 0, 2]], [2, 3, 3])])
def test_torch_sparse(idx_shape):
    from jina.ndarray.sparse.pytorch import SparseNdArray
    import torch
    i = torch.LongTensor(idx_shape[0])
    v = torch.FloatTensor([3, 4, 5])
    a = torch.sparse.FloatTensor(i, v, torch.Size(idx_shape[1]))

    b = SparseNdArray()
    b.value = a
    np.testing.assert_equal(b.value.to_dense().numpy(), a.to_dense().numpy())


def test_generic():
    from jina.ndarray.generic import GenericNdArray
    from scipy.sparse import coo_matrix

    row = np.array([0, 3, 1, 0])
    col = np.array([0, 3, 1, 2])
    data = np.array([4, 5, 7, 9])
    a = coo_matrix((data, (row, col)), shape=(4, 4))
    dense_a = a.toarray()

    b = GenericNdArray(is_sparse=True)

    # not set should raise empty value error
    with pytest.raises(ValueError):
        print(b.value)

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
