import numpy as np
import scipy.sparse as sp

from docarray.math.helper import minmax_normalize, update_rows_x_mat_best


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


def test_minmax_normalization_zero():
    a = np.array([[1, 1, 1], [3, 3, 3]])
    np.testing.assert_almost_equal(minmax_normalize(a), [[0, 0, 0], [0, 0, 0]])
    a_normalized = minmax_normalize(a, (1, 0))
    np.testing.assert_almost_equal(a_normalized, [[1, 1, 1], [1, 1, 1]])


def test_update_rows_x_mat_best():
    x_mat_best = np.array([[1, 5], [3, 5]])

    x_inds_best = np.array([[0, 1], [0, 1]])

    x_mat = np.array([[0, 1, 8, 9], [9, 8, 2, 1]])

    x_inds = np.array([[4, 5, 6, 7], [4, 5, 6, 7]])

    x_mat_best_produced, x_inds_best_produced = update_rows_x_mat_best(
        x_mat_best, x_inds_best, x_mat, x_inds, 2
    )

    x_mat_best_result = np.array([[0, 1], [1, 2]])
    x_inds_best_result = np.array([[4, 5], [7, 6]])

    np.testing.assert_almost_equal(x_mat_best_result, x_mat_best_produced)
    np.testing.assert_almost_equal(x_inds_best_result, x_inds_best_result)
