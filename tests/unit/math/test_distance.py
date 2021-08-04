import numpy as np
import pytest

from jina.math.distance import sqeuclidean, cosine, sparse_cosine, sparse_sqeuclidean
from jina.math.distance import cdist as jina_cdist
from jina.math.distance import pdist as jina_pdist

import scipy.sparse as sp
from scipy.spatial.distance import cdist, pdist


@pytest.fixture
def embeddings():
    return np.array([[1, 0, 0], [2, 0, 0], [3, 0, 0]])


@pytest.fixture
def embedding_query():
    return np.array([[1, 0, 0]])


@pytest.fixture
def other_embeddings():
    return np.array([[2, 0, 0], [3, 0, 0]])


@pytest.mark.parametrize(
    'func,data_type',
    [
        (cosine, np.array),
        (sparse_sqeuclidean, sp.csr_matrix),
        (sparse_sqeuclidean, sp.csc_matrix),
        (sparse_sqeuclidean, sp.coo_matrix),
        (sparse_sqeuclidean, sp.bsr_matrix),
    ],
)
def test_euclidean_distance_squared(func, data_type, embeddings, embedding_query):
    """
    embeddings = [[1,0,0],[2,0,0],[3,0,0]]
    embedding_query = [[1,0,0]]
    Should expect as output [[0,1,4]].T  because (1-1)**2 = 0, (2-1)**2 = 1, (3-1)**2 = 2**2 = 4
    """
    np.testing.assert_almost_equal(
        sqeuclidean(embedding_query, embeddings),
        np.array([[0, 1, 4]]),
    )


@pytest.mark.parametrize(
    'func,data_type',
    [
        (cosine, np.array),
        (sparse_cosine, sp.csr_matrix),
        (sparse_cosine, sp.csc_matrix),
        (sparse_cosine, sp.coo_matrix),
        (sparse_cosine, sp.bsr_matrix),
    ],
)
def test_cosine_distance_squared(func, data_type, embeddings, embedding_query):
    """
    embeddings = [[1,0,0],[2,0,0],[3,0,0]]
    embedding_query = [[1,0,0]]
    Should expect as output [[0,0,0]].T because query has same direction as every other element
    """
    np.testing.assert_almost_equal(
        func(data_type(embedding_query), data_type(embeddings)), np.array([[0, 0, 0]])
    )


@pytest.mark.parametrize(
    'metric, sparse_type',
    [
        ('cosine', sp.csr_matrix),
        ('cosine', sp.csc_matrix),
        ('cosine', sp.coo_matrix),
        ('cosine', sp.csr_matrix),
        ('sqeuclidean', sp.csr_matrix),
        ('sqeuclidean', sp.csc_matrix),
        ('sqeuclidean', sp.coo_matrix),
        ('sqeuclidean', sp.csr_matrix),
        ('euclidean', sp.csr_matrix),
        ('euclidean', sp.csc_matrix),
        ('euclidean', sp.coo_matrix),
        ('euclidean', sp.csr_matrix),
    ],
)
def test_cdist(metric, sparse_type, embeddings, other_embeddings):
    """
    Tests behaviour `jina.math.distance.cdist`  provides same results with sparse and dense versions.
    Moreover it tests that the provided results by Jina match the results given by `scipy.spatial.distance.cdist`
    """
    result_dense = jina_cdist(embeddings, other_embeddings, metric=metric)
    result_sparse = jina_cdist(
        sparse_type(embeddings),
        sparse_type(other_embeddings),
        metric=metric,
        is_sparse=True,
    )
    result_scipy = cdist(embeddings, other_embeddings, metric=metric)

    np.testing.assert_almost_equal(result_sparse, result_dense)
    np.testing.assert_almost_equal(result_dense, result_scipy)
    np.testing.assert_almost_equal(result_sparse, result_scipy)


def test_cdist_unkown_metric(embeddings):
    with pytest.raises(ValueError):
        jina_cdist(embeddings, embeddings, metric="Cosinatrus")


@pytest.mark.parametrize(
    'metric, sparse_type',
    [
        ('cosine', sp.csr_matrix),
        ('cosine', sp.csc_matrix),
        ('cosine', sp.coo_matrix),
        ('cosine', sp.csr_matrix),
        ('sqeuclidean', sp.csr_matrix),
        ('sqeuclidean', sp.csc_matrix),
        ('sqeuclidean', sp.coo_matrix),
        ('sqeuclidean', sp.csr_matrix),
        ('euclidean', sp.csr_matrix),
        ('euclidean', sp.csc_matrix),
        ('euclidean', sp.coo_matrix),
        ('euclidean', sp.csr_matrix),
    ],
)
def test_pdist(metric, sparse_type, embeddings, other_embeddings):
    """
    Tests behaviour `jina.math.distance.pdist`  provides same results with sparse and dense versions.
    """
    result_dense = jina_pdist(embeddings, metric=metric)
    result_sparse = jina_pdist(
        sparse_type(embeddings),
        metric=metric,
        is_sparse=True,
    )

    np.testing.assert_almost_equal(result_sparse, result_dense)


def test_new_distances_equal_previous_distances():
    def _get_ones(x, y):
        return np.ones((x, y))

    def _ext_A(A):
        nA, dim = A.shape
        A_ext = _get_ones(nA, dim * 3)
        A_ext[:, dim : 2 * dim] = A
        A_ext[:, 2 * dim :] = A ** 2
        return A_ext

    def _ext_B(B):
        nB, dim = B.shape
        B_ext = _get_ones(dim * 3, nB)
        B_ext[:dim] = (B ** 2).T
        B_ext[dim : 2 * dim] = -2.0 * B.T
        del B
        return B_ext

    def _euclidean(A_ext, B_ext):
        sqdist = A_ext.dot(B_ext).clip(min=0)
        return np.sqrt(sqdist)

    def _norm(A):
        return A / np.linalg.norm(A, ord=2, axis=1, keepdims=True)

    def _cosine(A_norm_ext, B_norm_ext):
        return A_norm_ext.dot(B_norm_ext).clip(min=0) / 2

    np.random.seed(1234)
    X = np.random.random((10, 10))
    Y = np.random.random((10, 10))

    ### test euclidean distance
    X_ext = _ext_A(X)
    Y_ext = _ext_B(Y)
    dists_previous_euclidean = _euclidean(X_ext, Y_ext)
    dists_new_euclidean = np.sqrt(sqeuclidean(X, Y))
    np.testing.assert_almost_equal(dists_previous_euclidean, dists_new_euclidean)

    ### test cosine distance
    X_ext = _ext_A(_norm(X))
    Y_ext = _ext_B(_norm(Y))
    dists_previous_cosine = _cosine(X_ext, Y_ext)
    dists_new_cosine = cosine(X, Y)
    np.testing.assert_almost_equal(dists_previous_cosine, dists_new_cosine)


def test_new_distances_equal_scipy_cdist():
    """
    Tests if current distance implementations match scipy.spatial.distance.cdist
    """
    X = np.array([[1, 1, 1], [4, 5, 6], [0, 1, 2]])
    Y = np.array([[1, 1, 2], [2, 3, 4]])

    XY_cdist = cdist(X, Y, metric="euclidean")
    XY_new = np.sqrt(sqeuclidean(X, Y))
    np.testing.assert_almost_equal(XY_cdist, XY_new)

    XY_cdist = cdist(X, Y, metric="cosine")
    XY_new = cosine(X, Y)
    np.testing.assert_almost_equal(XY_cdist, XY_new)
