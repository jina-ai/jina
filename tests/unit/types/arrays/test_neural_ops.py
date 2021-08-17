import copy
import os

import numpy as np
import scipy.sparse as sp
from scipy.spatial.distance import cdist as scipy_cdist
import pytest

from jina import Document, DocumentArray
from jina.types.arrays.memmap import DocumentArrayMemmap
from jina.math.dimensionality_reduction import PCA
from tests import random_docs


@pytest.fixture()
def doc_lists():
    d1 = Document(embedding=np.array([0, 0, 0]))
    d2 = Document(embedding=np.array([3, 0, 0]))
    d3 = Document(embedding=np.array([1, 0, 0]))
    d4 = Document(embedding=np.array([2, 0, 0]))

    d1_m = Document(embedding=np.array([1, 0, 0]))
    d2_m = Document(embedding=np.array([2, 0, 0]))
    d3_m = Document(embedding=np.array([0, 0, 1]))
    d4_m = Document(embedding=np.array([0, 0, 2]))
    d5_m = Document(embedding=np.array([0, 0, 3]))

    return [d1, d2, d3, d4], [d1_m, d2_m, d3_m, d4_m, d5_m]


@pytest.fixture
def docarrays_for_embedding_distance_computation(doc_lists):
    D1, D2 = doc_lists
    da1 = DocumentArray(D1)
    da2 = DocumentArray(D2)
    return da1, da2


@pytest.fixture
def docarrays_for_embedding_distance_computation_sparse():
    d1 = Document(embedding=sp.csr_matrix([0, 0, 0]))
    d2 = Document(embedding=sp.csr_matrix([3, 0, 0]))
    d3 = Document(embedding=sp.csr_matrix([1, 0, 0]))
    d4 = Document(embedding=sp.csr_matrix([2, 0, 0]))

    d1_m = Document(embedding=sp.csr_matrix([1, 0, 0]))
    d2_m = Document(embedding=sp.csr_matrix([2, 0, 0]))
    d3_m = Document(embedding=sp.csr_matrix([0, 0, 1]))
    d4_m = Document(embedding=sp.csr_matrix([0, 0, 2]))
    d5_m = Document(embedding=sp.csr_matrix([0, 0, 3]))

    D1 = DocumentArray([d1, d2, d3, d4])
    D2 = DocumentArray([d1_m, d2_m, d3_m, d4_m, d5_m])
    return D1, D2


@pytest.fixture
def embeddings():
    return np.array([[1, 0, 0], [2, 0, 0], [3, 0, 0]])


def doc_lists_to_doc_arrays(
    doc_lists, tmpdir, first_memmap, second_memmap, buffer_pool_size
):
    doc_list1, doc_list2 = doc_lists

    tmpdir1, tmpdir2 = tmpdir / '1', tmpdir / '2'

    D1 = (
        DocumentArray()
        if not first_memmap
        else DocumentArrayMemmap(tmpdir1, buffer_pool_size=buffer_pool_size)
    )
    D1.extend(doc_list1)
    D2 = (
        DocumentArray()
        if not second_memmap
        else DocumentArrayMemmap(tmpdir2, buffer_pool_size=buffer_pool_size)
    )
    D2.extend(doc_list2)
    return D1, D2


@pytest.mark.parametrize('buffer_pool_size', [1000, 3])
@pytest.mark.parametrize('first_memmap', [True, False])
@pytest.mark.parametrize('second_memmap', [True, False])
@pytest.mark.parametrize(
    'limit, batch_size', [(1, None), (2, None), (None, None), (1, 1), (1, 2), (2, 1)]
)
def test_matching_retrieves_correct_number(
    doc_lists, limit, batch_size, first_memmap, second_memmap, tmpdir, buffer_pool_size
):
    D1, D2 = doc_lists_to_doc_arrays(
        doc_lists,
        tmpdir,
        first_memmap,
        second_memmap,
        buffer_pool_size=buffer_pool_size,
    )
    D1.match(D2, metric='sqeuclidean', limit=limit, batch_size=batch_size)
    for m in D1.get_attributes('matches'):
        if limit is None:
            assert len(m) == len(D2)
        else:
            assert len(m) == limit


@pytest.mark.parametrize('metric', ['sqeuclidean', 'cosine'])
def test_matching_same_results_with_sparse(
    docarrays_for_embedding_distance_computation,
    docarrays_for_embedding_distance_computation_sparse,
    metric,
):

    D1, D2 = docarrays_for_embedding_distance_computation
    D1_sp, D2_sp = docarrays_for_embedding_distance_computation_sparse

    # use match with numpy arrays
    D1.match(D2, metric=metric)
    distances = []
    for m in D1.get_attributes('matches'):
        for d in m:
            distances.extend([d.scores[metric].value])

    # use match with sparse arrays
    D1_sp.match(D2_sp, metric=metric)
    distances_sparse = []
    for m in D1.get_attributes('matches'):
        for d in m:
            distances_sparse.extend([d.scores[metric].value])

    np.testing.assert_equal(distances, distances_sparse)


@pytest.mark.parametrize('metric', ['sqeuclidean', 'cosine'])
def test_matching_same_results_with_batch(
    docarrays_for_embedding_distance_computation,
    metric,
):

    D1, D2 = docarrays_for_embedding_distance_computation
    D1_batch = copy.deepcopy(D1)
    D2_batch = copy.deepcopy(D2)

    # use match without batches
    D1.match(D2, metric=metric)
    distances = []
    for m in D1.get_attributes('matches'):
        for d in m:
            distances.extend([d.scores[metric].value])

    # use match with batches
    D1_batch.match(D2_batch, metric=metric, batch_size=10)

    distances_batch = []
    for m in D1.get_attributes('matches'):
        for d in m:
            distances_batch.extend([d.scores[metric].value])

    np.testing.assert_equal(distances, distances_batch)


@pytest.mark.parametrize('metric', ['euclidean', 'cosine'])
def test_matching_scipy_cdist(
    docarrays_for_embedding_distance_computation,
    metric,
):
    def scipy_cdist_metric(X, Y, *args):
        return scipy_cdist(X, Y, metric=metric)

    D1, D2 = docarrays_for_embedding_distance_computation
    D1_scipy = copy.deepcopy(D1)

    # match with our custom metric
    D1.match(D2, metric=metric)
    distances = []
    for m in D1.get_attributes('matches'):
        for d in m:
            distances.extend([d.scores[metric].value])

    # match with callable cdist function from scipy
    D1_scipy.match(D2, metric=scipy_cdist_metric)
    distances_scipy = []
    for m in D1.get_attributes('matches'):
        for d in m:
            distances_scipy.extend([d.scores[metric].value])

    np.testing.assert_equal(distances, distances_scipy)


@pytest.mark.parametrize('buffer_pool_size', [1000, 3])
@pytest.mark.parametrize('first_memmap', [True, False])
@pytest.mark.parametrize('second_memmap', [True, False])
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
    doc_lists,
    tmpdir,
    normalization,
    metric,
    use_scipy,
    first_memmap,
    second_memmap,
    buffer_pool_size,
):
    """
    Tests if match.values are returned 'low to high' if normalization is True or 'high to low' otherwise
    """
    D1, D2 = doc_lists_to_doc_arrays(
        doc_lists,
        tmpdir,
        first_memmap,
        second_memmap,
        buffer_pool_size=buffer_pool_size,
    )
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
    D1_.match(
        D2memmap,
        metric=metric,
        limit=3,
        normalization=normalization,
        use_scipy=use_scipy,
    )
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


@pytest.mark.parametrize('buffer_pool_size', [1000, 3])
@pytest.mark.parametrize('first_memmap', [True, False])
@pytest.mark.parametrize('second_memmap', [True, False])
def test_2arity_function(
    first_memmap, second_memmap, doc_lists, tmpdir, buffer_pool_size
):
    def dotp(x, y, *args):
        return np.dot(x, np.transpose(y))

    D1, D2 = doc_lists_to_doc_arrays(
        doc_lists,
        tmpdir,
        first_memmap,
        second_memmap,
        buffer_pool_size=buffer_pool_size,
    )
    D1.match(D2, metric=dotp, use_scipy=True)

    for d in D1:
        for m in d.matches:
            assert 'dotp' in m.scores


@pytest.mark.parametrize('whiten', [True, False])
def test_pca_projection(embeddings, whiten):
    n_components = 2
    n_features = embeddings.shape[1]
    pca = PCA(n_components=n_components, whiten=whiten)
    assert pca.e_values is None
    assert pca.w is None
    embeddings_transformed = pca.fit_transform(embeddings)
    assert len(pca.e_values) == n_features
    assert pca.w.shape[0] == n_features
    assert embeddings_transformed.shape[1] == n_components


def test_pca_plot_generated(embeddings, tmpdir):
    doc_array = DocumentArray([Document(embedding=x) for x in embeddings])
    file_path = os.path.join(tmpdir, 'pca_plot.png')
    doc_array.visualize(output=file_path)
    assert os.path.exists(file_path)


def test_match_inclusive():
    """Call match function, while the other :class:`DocumentArray` is itself
    or have same :class:`Document`.
    """
    # The document array da1 match with itself.
    da1 = DocumentArray(
        [
            Document(embedding=np.array([1, 2, 3])),
            Document(embedding=np.array([1, 0, 1])),
            Document(embedding=np.array([1, 1, 2])),
        ]
    )

    da1.match(da1)
    assert len(da1) == 3
    traversed = da1.traverse_flat(traversal_paths=['m', 'mm', 'mmm'])
    assert len(traversed) == 9
    # The document array da2 shares same documents with da1
    da2 = DocumentArray([Document(embedding=np.array([4, 1, 3])), da1[0], da1[1]])
    da1.match(da2)
    assert len(da2) == 3
    traversed = da1.traverse_flat(traversal_paths=['m', 'mm', 'mmm'])
    assert len(traversed) == 9


def test_match_inclusive_dam(tmpdir):
    """Call match function, while the other :class:`DocumentArray` is itself
    or have same :class:`Document`.
    """
    # The document array da1 match with itself.
    dam = DocumentArrayMemmap(tmpdir)
    dam.extend(
        [
            Document(embedding=np.array([1, 2, 3])),
            Document(embedding=np.array([1, 0, 1])),
            Document(embedding=np.array([1, 1, 2])),
        ]
    )

    dam.match(dam)
    assert len(dam) == 3
    traversed = dam.traverse_flat(traversal_paths=['m', 'mm', 'mmm'])
    assert len(list(traversed)) == 9
    # The document array da2 shares same documents with da1
    da2 = DocumentArray([Document(embedding=np.array([4, 1, 3])), dam[0], dam[1]])
    dam.match(da2)
    assert len(da2) == 3
    traversed = dam.traverse_flat(traversal_paths=['m', 'mm', 'mmm'])
    assert len(list(traversed)) == 9


def test_da_get_embeddings():
    da = DocumentArray(random_docs(100))
    np.testing.assert_almost_equal(da.get_attributes('embedding'), da.embeddings)


def test_dam_embeddings(tmpdir):
    dam = DocumentArrayMemmap(tmpdir)
    dam.extend(Document(embedding=np.array([1, 2, 3, 4])) for _ in range(100))
    np.testing.assert_almost_equal(dam.get_attributes('embedding'), dam.embeddings)


def test_da_get_embeddings():
    da = DocumentArray(random_docs(100))
    np.testing.assert_almost_equal(
        da.get_attributes('embedding')[10:20], da._get_embeddings(slice(10, 20))
    )


def test_dam_get_embeddings(tmpdir):
    da = DocumentArrayMemmap(tmpdir)
    da.extend(Document(embedding=np.array([1, 2, 3, 4])) for _ in range(100))
    np.testing.assert_almost_equal(
        da.get_attributes('embedding')[10:20], da._get_embeddings(slice(10, 20))
    )


def test_embeddings_setter():
    emb = np.random.random((100, 128))
    da = DocumentArray([Document() for _ in range(100)])
    da.embeddings = emb
    np.testing.assert_almost_equal(da.embeddings, emb)


def test_embeddings_getter():
    emb = np.random.random((100, 128))
    da = DocumentArray([Document(embedding=x) for x in emb])
    np.testing.assert_almost_equal(da.embeddings, emb)
