import copy

import numpy as np
import pytest

from jina import Document, DocumentArray
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


@pytest.mark.parametrize('limit', [1, 2])
def test_matching_retrieves_correct_number(
    docarrays_for_embedding_distance_computation, limit
):
    D1, D2 = docarrays_for_embedding_distance_computation
    D1.match(D2, metric='sqeuclidean', limit=limit)
    for m in D1.get_attributes('matches'):
        assert len(m) == limit


@pytest.mark.parametrize(
    'normalization, metric',
    [
        (None, 'sqeuclidean'),
        ((0, 1), 'sqeuclidean'),
        (None, 'euclidean'),
        ((0, 1), 'euclidean'),
        (None, 'cosine'),
        ((0, 1), 'cosine'),
    ],
)
@pytest.mark.parametrize('use_scipy', [True, False])
def test_matching_retrieves_closest_matches(
    docarrays_for_embedding_distance_computation, normalization, metric, use_scipy
):
    """
    Tests if match.values are returned 'low to high' if normalization is True or 'high to low' otherwise
    """
    D1, D2 = docarrays_for_embedding_distance_computation
    D1.match(
        D2, metric=metric, limit=3, normalization=normalization, use_scipy=use_scipy
    )
    expected_sorted_values = [
        D1[0].matches[i].scores['sqeuclidean'].value for i in range(3)
    ]
    if normalization:
        assert min(expected_sorted_values) >= 0
        assert max(expected_sorted_values) <= 1
    else:
        assert expected_sorted_values == sorted(expected_sorted_values)


@pytest.mark.parametrize(
    'normalization, metric',
    [
        (None, 'sqeuclidean'),
        ((0, 1), 'sqeuclidean'),
        (None, 'euclidean'),
        ((0, 1), 'euclidean'),
        (None, 'cosine'),
        ((0, 1), 'cosine'),
    ],
)
@pytest.mark.parametrize('use_scipy', [True, False])
def test_docarray_match_docarraymemmap(
    docarrays_for_embedding_distance_computation,
    normalization,
    metric,
    tmpdir,
    use_scipy,
):
    D1, D2 = docarrays_for_embedding_distance_computation
    D1_ = copy.deepcopy(D1)
    D2_ = copy.deepcopy(D2)
    D1.match(
        D2, metric=metric, limit=3, normalization=normalization, use_scipy=use_scipy
    )
    values_docarray = [m.scores[metric].value for d in D1 for m in d.matches]

    D2memmap = DocumentArrayMemmap(tmpdir)
    D2memmap.extend(D2_)
    D1_.match(D2memmap, metric=metric, limit=3, normalization=normalization)
    values_docarraymemmap = [m.scores[metric].value for d in D1_ for m in d.matches]

    np.testing.assert_equal(values_docarray, values_docarraymemmap)


@pytest.mark.parametrize(
    'normalization, metric',
    [
        (None, 'hamming'),
        ((0, 1), 'hamming'),
        (None, 'minkowski'),
        ((0, 1), 'minkowski'),
        (None, 'jaccard'),
        ((0, 1), 'jaccard'),
    ],
)
def test_scipy_dist(
    docarrays_for_embedding_distance_computation, normalization, metric, tmpdir
):
    D1, D2 = docarrays_for_embedding_distance_computation
    D1_ = copy.deepcopy(D1)
    D2_ = copy.deepcopy(D2)
    D1.match(D2, metric=metric, limit=3, normalization=normalization, use_scipy=True)
    values_docarray = [m.scores[metric].value for d in D1 for m in d.matches]

    D2memmap = DocumentArrayMemmap(tmpdir)
    D2memmap.extend(D2_)
    D1_.match(
        D2memmap, metric=metric, limit=3, normalization=normalization, use_scipy=True
    )
    values_docarraymemmap = [m.scores[metric].value for d in D1_ for m in d.matches]

    np.testing.assert_equal(values_docarray, values_docarraymemmap)


def test_2arity_function(docarrays_for_embedding_distance_computation):
    def dotp(x, y):
        return np.dot(x, np.transpose(y))

    D1, D2 = docarrays_for_embedding_distance_computation
    D1.match(D2, metric=dotp, use_scipy=True)

    for d in D1:
        for m in d.matches:
            assert 'dotp' in m.scores
