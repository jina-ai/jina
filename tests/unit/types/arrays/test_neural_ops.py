import copy

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from jina import Document, DocumentArray
from jina.math.distance import sqeuclidean, cosine
from jina.types.arrays.memmap import DocumentArrayMemmap


@pytest.fixture
def docarrays_for_embedding_distance_computation():
    d1 = Document(embedding=np.array([0, 0, 0]))
    d2 = Document(embedding=np.array([3, 0, 0]))
    d3 = Document(embedding=np.array([1, 0, 0]))
    d4 = Document(embedding=np.array([2, 0, 0]))

    d1_m = Document(embedding=np.array([1, 0, 0]))
    d2_m = Document(embedding=np.array([2, 0, 0]))
    d3_m = Document(embedding=np.array([0, 0, 1]))
    d4_m = Document(embedding=np.array([0, 0, 2]))
    d5_m = Document(embedding=np.array([0, 0, 3]))

    D1 = DocumentArray([d1, d2, d3, d4])
    D2 = DocumentArray([d1_m, d2_m, d3_m, d4_m, d5_m])
    return D1, D2


@pytest.fixture
def embeddings():
    return np.array([[1, 0, 0], [2, 0, 0], [3, 0, 0]])


@pytest.fixture
def embedding_query():
    return np.array([[1, 0, 0]])


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

    XY_cdist = cdist(X, Y, metric='euclidean')
    XY_new = np.sqrt(sqeuclidean(X, Y))
    np.testing.assert_almost_equal(XY_cdist, XY_new)

    XY_cdist = cdist(X, Y, metric='cosine')
    XY_new = cosine(X, Y)
    np.testing.assert_almost_equal(XY_cdist, XY_new)


@pytest.mark.parametrize('limit', [1, 2])
def test_matching_retrieves_correct_number(
    docarrays_for_embedding_distance_computation, limit
):
    D1, D2 = docarrays_for_embedding_distance_computation
    D1.match(D2, metric='sqeuclidean', limit=limit, is_distance=True)
    for m in D1.get_attributes('matches'):
        assert len(m) == limit


@pytest.mark.parametrize(
    'is_distance, metric',
    [
        (True, 'sqeuclidean'),
        (False, 'sqeuclidean'),
        (True, 'euclidean'),
        (False, 'euclidean'),
        (True, 'cosine'),
        (False, 'cosine'),
    ],
)
def test_matching_retrieves_closest_matches(
    docarrays_for_embedding_distance_computation, is_distance, metric
):
    """
    Tests if match.values are returned 'low to high' if is_distance is True or 'high to low' otherwise
    """
    D1, D2 = docarrays_for_embedding_distance_computation
    D1.match(D2, metric=metric, limit=3, is_distance=is_distance)
    expected_sorted_values = [
        D1[0].get_attributes('matches')[i].scores['sqeuclidean'].value for i in range(3)
    ]
    if is_distance:
        assert expected_sorted_values == sorted(expected_sorted_values)
    else:
        assert expected_sorted_values == sorted(expected_sorted_values)[::-1]


def test_euclidean_distance_squared(embeddings, embedding_query):
    """
    embeddings = [[1,0,0],[2,0,0],[3,0,0]]
    embedding_query = [[1,0,0]]
    Should expect as output [[0,1,4]].T  because (1-1)**2 = 0, (2-1)**2 = 1, (3-1)**2 = 2**2 = 4
    """
    np.testing.assert_almost_equal(
        sqeuclidean(embedding_query, embeddings),
        np.array([[0, 1, 4]]),
    )


def test_cosine_distance_squared(embeddings, embedding_query):
    """
    embeddings = [[1,0,0],[2,0,0],[3,0,0]]
    embedding_query = [[1,0,0]]
    Should expect as output [[0,0,0]].T because query has same direction as every other element
    """
    np.testing.assert_almost_equal(
        cosine(embedding_query, embeddings), np.array([[0, 0, 0]])
    )


@pytest.mark.parametrize(
    'is_distance, metric',
    [
        (True, 'sqeuclidean'),
        (False, 'sqeuclidean'),
        (True, 'euclidean'),
        (False, 'euclidean'),
        (True, 'cosine'),
        (False, 'cosine'),
    ],
)
def test_docarray_match_docarraymemmap(
    docarrays_for_embedding_distance_computation, is_distance, metric, tmpdir
):
    D1, D2 = docarrays_for_embedding_distance_computation
    D1_ = copy.deepcopy(D1)
    D2_ = copy.deepcopy(D2)
    D1.match(D2, metric=metric, limit=3, is_distance=is_distance)
    values_docarray = [m.scores[metric].value for d in D1 for m in d.matches]

    D2memmap = DocumentArrayMemmap(tmpdir)
    D2memmap.extend(D2_)
    D1_.match(D2memmap, metric=metric, limit=3, is_distance=is_distance)
    values_docarraymemmap = [m.scores[metric].value for d in D1_ for m in d.matches]

    np.testing.assert_equal(values_docarray, values_docarraymemmap)
