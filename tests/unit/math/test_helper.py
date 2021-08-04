import numpy as np
import scipy.sparse as sp

from jina.math.helper import minmax_normalize


def test_minmax_normalization_1d():
    a = np.array([1, 2, 3])
    np.testing.assert_almost_equal(minmax_normalize(a), [0, 0.5, 1])
    a_normalized = minmax_normalize(a, (1, 0))
    np.testing.assert_almost_equal(a_normalized, [1, 0.5, 0])


def test_minmax_normalization_2d():
    a = np.array([[1, 2, 3], [3, 2, 1]])
    np.testing.assert_almost_equal(minmax_normalize(a), [[0, 0.5, 1], [1, 0.5, 0]])
    a_normalized = minmax_normalize(a, (1, 0))
    np.testing.assert_almost_equal(a_normalized, [[1, 0.5, 0], [0, 0.5, 1]])


def test_minmax_normalization_sparse():
    a = sp.csr_matrix([[1, 2, 3], [3, 2, 1]])
    np.testing.assert_almost_equal(minmax_normalize(a), [[0, 0.5, 1], [1, 0.5, 0]])
    a_normalized = minmax_normalize(a, (1, 0))
    np.testing.assert_almost_equal(a_normalized, [[1, 0.5, 0], [0, 0.5, 1]])
