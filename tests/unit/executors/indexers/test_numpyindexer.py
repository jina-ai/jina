import os

import numpy as np
import pytest

from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.vector import NumpyIndexer

# fix the seed here

np.random.seed(500)
retr_idx = None
num_data = 100
num_dim = 64
num_query = 10
vec_idx = np.array(
    np.random.randint(0, high=num_data, size=[num_data]), dtype=(np.str_, 16)
)
vec = np.random.random([num_data, num_dim])
query = np.array(np.random.random([num_query, num_dim]), dtype=np.float32)


@pytest.mark.parametrize(
    'batch_size, compress_level', [(None, 0), (None, 1), (2, 0), (2, 1)]
)
def test_numpy_indexer(batch_size, compress_level, test_metas):
    with NumpyIndexer(
        metric='euclidean',
        index_filename='np.test.gz',
        compress_level=compress_level,
        metas=test_metas,
    ) as indexer:
        indexer.batch_size = batch_size
        indexer.add(vec_idx, vec)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        if compress_level == 0:
            assert isinstance(indexer.query_handler, np.memmap)
        idx, dist = indexer.query(query, top_k=4)
        assert idx.shape == dist.shape
        assert idx.shape == (num_query, 4)


def test_numpy_indexer_long_ids(test_metas):
    with NumpyIndexer(
        metric='euclidean',
        index_filename='np.test.gz',
        compress_level=0,
        metas=test_metas,
    ) as indexer:
        indexer.batch_size = 4
        long_vec_id = np.array(vec_idx, dtype=(np.str_, 20))
        long_vec_id[0] = '1234512345123451234'
        indexer.add(long_vec_id, vec)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        idx, dist = indexer.query(query, top_k=4)
        assert idx.shape == dist.shape
        assert idx.shape == (num_query, 4)


def test_numpy_indexer_assert_shape_mismatch(test_metas):
    with NumpyIndexer(
        metric='euclidean',
        index_filename='np.test.gz',
        compress_level=0,
        metas=test_metas,
    ) as indexer:
        indexer.batch_size = 4
        vec_short = np.array([[1, 1, 1], [2, 2, 2]])
        vec_keys = np.array([1, 2, 3])
        with pytest.raises(ValueError):
            indexer.add(vec_keys, vec_short)


@pytest.mark.parametrize(
    'batch_size, compress_level', [(None, 0), (None, 1), (16, 0), (16, 1)]
)
def test_numpy_indexer_known(batch_size, compress_level, test_metas):
    vectors = np.array([[1, 1, 1], [10, 10, 10], [100, 100, 100], [1000, 1000, 1000]])
    keys = np.array(['4', '5', '6', '7'], dtype=(np.str_, 16))
    with NumpyIndexer(
        metric='euclidean',
        index_filename='np.test.gz',
        compress_level=compress_level,
        metas=test_metas,
    ) as indexer:
        indexer.batch_size = batch_size
        indexer.add(keys, vectors)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    queries = np.array([[1, 1, 1], [10, 10, 10], [100, 100, 100], [1000, 1000, 1000]])
    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        if compress_level == 0:
            assert isinstance(indexer.query_handler, np.memmap)
        idx, dist = indexer.query(queries, top_k=2)
        np.testing.assert_equal(
            idx, np.array([['4', '5'], ['5', '4'], ['6', '5'], ['7', '6']])
        )
        assert idx.shape == dist.shape
        assert idx.shape == (4, 2)
        np.testing.assert_equal(indexer.query_by_key(['7', '4']), vectors[[3, 0]])


@pytest.mark.parametrize(
    'batch_size, compress_level', [(None, 0), (None, 1), (16, 0), (16, 1)]
)
def test_scipy_indexer(batch_size, compress_level, test_metas):
    with NumpyIndexer(
        metric='euclidean',
        index_filename='np.test.gz',
        backend='scipy',
        compress_level=compress_level,
        metas=test_metas,
    ) as indexer:
        indexer.batch_size = batch_size
        indexer.add(vec_idx, vec)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        if compress_level == 0:
            assert isinstance(indexer.query_handler, np.memmap)
        idx, dist = indexer.query(query, top_k=4)
        assert idx.shape == dist.shape
        assert idx.shape == (num_query, 4)


@pytest.mark.parametrize(
    'batch_size, compress_level', [(None, 0), (None, 1), (16, 0), (16, 1)]
)
def test_numpy_indexer_known_big(batch_size, compress_level, test_metas):
    """Let's try to have some real test. We will have an index with 10k vectors of random values between 5 and 10.
    We will change tweak some specific vectors that we expect to be retrieved at query time. We will tweak vector
    at index [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000], this will also be the query vectors.
    Then the keys will be assigned shifted to test the proper usage of `int2ext_id` and `ext2int_id`
    """
    vectors = np.random.uniform(low=5.0, high=10.0, size=(10000, 1024))

    queries = np.empty((10, 1024))
    for idx in range(0, 10000, 1000):
        array = idx * np.ones((1, 1024))
        queries[int(idx / 1000)] = array
        vectors[idx] = array

    # TODO: PLLEASE DO NOT BUILD FLAKY KEYS LIKE THIS
    keys = np.squeeze(
        np.array(np.arange(10000, 20000).reshape(-1, 1), dtype=(np.str_, 16))
    )

    with NumpyIndexer(
        metric='euclidean',
        index_filename='np.test.gz',
        compress_level=compress_level,
        metas=test_metas,
    ) as indexer:
        indexer.add(keys, vectors)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        if compress_level == 0:
            assert isinstance(indexer.query_handler, np.memmap)
        idx, dist = indexer.query(queries, top_k=1)
        np.testing.assert_equal(
            idx,
            np.array(
                [
                    ['10000'],
                    ['11000'],
                    ['12000'],
                    ['13000'],
                    ['14000'],
                    ['15000'],
                    ['16000'],
                    ['17000'],
                    ['18000'],
                    ['19000'],
                ]
            ),
        )
        assert idx.shape == dist.shape
        assert idx.shape == (10, 1)
        np.testing.assert_equal(
            indexer.query_by_key(['10000', '15000']), vectors[[0, 5000]]
        )


@pytest.mark.parametrize('compress_level', [0, 1, 2, 3, 4, 5])
def test_scipy_indexer_known_big(compress_level, test_metas):
    """Let's try to have some real test. We will have an index with 10k vectors of random values between 5 and 10.
    We will change tweak some specific vectors that we expect to be retrieved at query time. We will tweak vector
    at index [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000], this will also be the query vectors.
    Then the keys will be assigned shifted to test the proper usage of `int2ext_id` and `ext2int_id`
    """
    vectors = np.random.uniform(low=5.0, high=10.0, size=(10000, 1024))

    queries = np.empty((10, 1024))
    for idx in range(0, 10000, 1000):
        array = idx * np.ones((1, 1024))
        queries[int(idx / 1000)] = array
        vectors[idx] = array

    keys = np.squeeze(
        np.array(np.arange(10000, 20000).reshape(-1, 1), dtype=(np.str_, 16))
    )

    with NumpyIndexer(
        metric='euclidean',
        index_filename='np.test.gz',
        backend='scipy',
        compress_level=compress_level,
        metas=test_metas,
    ) as indexer:
        indexer.add(keys, vectors)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        if compress_level == 0:
            assert isinstance(indexer.query_handler, np.memmap)
        idx, dist = indexer.query(queries, top_k=1)
        np.testing.assert_equal(
            idx,
            np.array(
                [
                    ['10000'],
                    ['11000'],
                    ['12000'],
                    ['13000'],
                    ['14000'],
                    ['15000'],
                    ['16000'],
                    ['17000'],
                    ['18000'],
                    ['19000'],
                ]
            ),
        )
        assert idx.shape == dist.shape
        assert idx.shape == (10, 1)
        np.testing.assert_equal(
            indexer.query_by_key(['10000', '15000']), vectors[[0, 5000]]
        )


@pytest.mark.parametrize(
    'batch_size, num_docs, top_k',
    [(1, 10, 1), (1, 10, 10), (10, 1, 1), (10, 1000, 10), (10, 10, 100)],
)
def test__get_sorted_top_k(batch_size, num_docs, top_k, test_metas):
    dist = np.random.uniform(size=(batch_size, num_docs))

    expected_idx = np.argsort(dist)[:, :top_k]
    expected_dist = np.sort(dist)[:, :top_k]

    with NumpyIndexer(metric='euclidean', metas=test_metas) as indexer:
        idx, dist = indexer._get_sorted_top_k(dist, top_k=top_k)

        np.testing.assert_equal(idx, expected_idx)
        np.testing.assert_equal(dist, expected_dist)


@pytest.mark.parametrize(
    'batch_size, compress_level', [(None, 0), (None, 1), (2, 0), (2, 1)]
)
def test_numpy_indexer_empty_data(batch_size, compress_level, test_metas):
    idx_file_path = os.path.join(test_metas['workspace'], 'np.test.gz')
    with NumpyIndexer(
        index_filename=str(idx_file_path),
        compress_level=compress_level,
        metas=test_metas,
    ) as indexer:
        indexer.batch_size = batch_size
        indexer.touch()
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        idx, dist = indexer.query(query, top_k=4)
        assert len(idx) == 0
        assert len(dist) == 0


@pytest.mark.parametrize('metric', ['euclidean', 'cosine'])
def test_indexer_one_dimensional(metric, test_metas):
    import math

    add_vec_idx = np.array(['0'], dtype=(np.str_, 16))
    add_vec = np.asarray([[1]])
    query_vec = np.asarray([[2]])
    with NumpyIndexer(
        metric=metric, index_filename='np.test.gz', metas=test_metas
    ) as indexer:
        indexer.add(add_vec_idx, add_vec)

        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        assert isinstance(indexer.query_handler, np.memmap)
        idx, dist = indexer.query(query_vec, top_k=4)
        assert idx.shape == dist.shape
        assert idx.shape == (1, 1)
        assert not math.isnan(dist[0])


@pytest.mark.parametrize('dimension', [1, 64])
@pytest.mark.parametrize('metric', ['euclidean', 'cosine'])
def test_indexer_zeros(metric, dimension, test_metas):
    import math

    query_vec = np.array(np.zeros([1, dimension]), dtype=np.float32)
    add_vec_idx = np.array(
        np.random.randint(0, high=num_data, size=[num_data]), dtype=(np.str_, 16)
    )
    add_vec = np.random.random([num_data, dimension])
    with NumpyIndexer(
        metric=metric, index_filename='np.test.gz', metas=test_metas
    ) as indexer:
        indexer.add(add_vec_idx, add_vec)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        assert isinstance(indexer.query_handler, np.memmap)
        idx, dist = indexer.query(query_vec, top_k=4)

        assert idx.shape == dist.shape
        assert idx.shape == (1, 4)
        if metric == 'cosine':
            assert all(math.isnan(x) for x in dist[0])
        else:
            assert not any(math.isnan(x) for x in dist[0])


@pytest.mark.parametrize('real_delete', [True, False])
@pytest.mark.parametrize('compress_level', [0, 1, 2, 3, 4, 5])
def test_numpy_update_delete_delete_on_dump(compress_level, real_delete, test_metas):
    np.random.seed(500)
    num_dim = 3
    vec_idx = np.array(['12', '112', '903'], dtype=(np.str_, 16))
    vec = np.random.random([len(vec_idx), num_dim])

    with NumpyIndexer(
        metric='euclidean',
        index_filename='np.test.gz',
        compress_level=compress_level,
        metas=test_metas,
        delete_on_dump=real_delete,
    ) as indexer:
        indexer.add(vec_idx, vec)
        indexer.save()
        assert indexer.num_dim == num_dim
        assert indexer.size == len(vec_idx)
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        query_results = indexer.query_by_key(vec_idx)
        assert np.array_equal(vec, query_results)

    # update
    key_to_update = vec_idx[0]
    data_to_update = np.random.random([1, num_dim])
    # nonexistent key
    random_keys = np.array(['999'], dtype=(np.str_, 16))
    random_data = np.random.random([1, num_dim])

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        # NON-EXISTENT KEYS: this will log warning but not fail
        indexer.update(random_keys, random_data)
        indexer.update([key_to_update], data_to_update)
        indexer.save()

    with BaseIndexer.load(save_abspath) as indexer:
        # this tests the real delete
        if real_delete:
            assert len(indexer.valid_indices) == indexer.size
        else:
            assert len(indexer.valid_indices) != indexer.size
        assert isinstance(indexer, NumpyIndexer)
        query_results = indexer.query_by_key([key_to_update])
        assert np.array_equal(data_to_update, query_results)

    # delete
    keys_to_delete = 1
    vec_idx_to_delete = vec_idx[:keys_to_delete]

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        indexer.delete(vec_idx_to_delete)
        indexer.save()
        assert indexer.size == len(vec_idx) - keys_to_delete

    assert indexer.size == len(vec_idx) - keys_to_delete

    with BaseIndexer.load(save_abspath) as indexer:
        # this tests the real delete
        if real_delete:
            assert len(indexer.valid_indices) == indexer.size
        else:
            assert len(indexer.valid_indices) != indexer.size
        assert isinstance(indexer, NumpyIndexer)
        assert indexer.size == len(vec_idx) - keys_to_delete
        # random non-existent key
        assert indexer.query_by_key(['123861942']) is None
        query_results = indexer.query_by_key(vec_idx[keys_to_delete:])
        expected = vec[keys_to_delete:]
        np.testing.assert_allclose(query_results, expected, equal_nan=True)


@pytest.mark.parametrize(
    'batch_size, compress_level', [(None, 0), (None, 1), (16, 0), (16, 1)]
)
def test_numpy_indexer_known_and_delete_delete_dump(
    batch_size, compress_level, test_metas
):
    vectors = np.array([[1, 1, 1], [10, 10, 10], [100, 100, 100]])
    keys = np.array(['4', '5', '6'], dtype=(np.str_, 16))
    with NumpyIndexer(
        metric='euclidean',
        index_filename='np.test.gz',
        compress_level=compress_level,
        metas=test_metas,
        delete_on_dump=True,
    ) as indexer:
        indexer.batch_size = batch_size
        indexer.add(keys, vectors)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        save_abspath = indexer.save_abspath

    top_k = 3
    queries = np.array([[1, 1, 1], [10, 10, 10]])
    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        idx, dist = indexer.query(queries, top_k=top_k)
        np.testing.assert_equal(idx, np.array([['4', '5', '6'], ['5', '4', '6']]))
        assert idx.shape == dist.shape
        assert idx.shape == (len(queries), top_k)
        np.testing.assert_equal(
            indexer.query_by_key(['5', '4', '6']), vectors[[1, 0, 2]]
        )

    # update and query again
    key_to_update = np.array(['4'])
    data_to_update = np.array([[1000, 1000, 1000]])

    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        indexer.update(key_to_update, data_to_update)
        indexer.save()

    with BaseIndexer.load(save_abspath) as indexer:
        # this tests the real delete
        assert len(indexer.valid_indices) == indexer.size
        assert isinstance(indexer, NumpyIndexer)
        idx, dist = indexer.query(queries, top_k=top_k)
        np.testing.assert_equal(idx, np.array([['5', '6', '4'], ['5', '6', '4']]))
        assert idx.shape == dist.shape
        assert idx.shape == (len(queries), top_k)

    # delete and query again
    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        indexer.delete([4])
        indexer.save()

    top_k = 2
    queries = np.array([[100, 100, 100], [10, 10, 10]])
    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        idx, dist = indexer.query(queries, top_k=2)
        np.testing.assert_equal(idx, np.array([['6', '5'], ['5', '6']]))
        assert idx.shape == dist.shape
        assert idx.shape == (len(queries), top_k)
        np.testing.assert_equal(indexer.query_by_key(['6', '5']), vectors[[2, 1]])

    # test query by nonexistent key
    with BaseIndexer.load(save_abspath) as indexer:
        assert isinstance(indexer, NumpyIndexer)
        assert indexer.query_by_key(['91237124']) is None


@pytest.mark.parametrize('compress_level', [0, 1, 2, 3])
def test_numpy_indexer_with_ref_indexer(compress_level, test_metas):
    vectors = np.array([[1, 1, 1], [10, 10, 10], [100, 100, 100], [1000, 1000, 1000]])
    keys = np.array(['4', '5', '6', '7'], dtype=(np.str_, 16))
    with NumpyIndexer(
        metric='euclidean',
        index_filename='np.test.gz',
        compress_level=compress_level,
        metas=test_metas,
    ) as indexer:
        indexer.add(keys, vectors)
        indexer.save()
        assert os.path.exists(indexer.index_abspath)
        index_filename = indexer.index_filename

    queries = np.array([[1, 1, 1], [10, 10, 10], [100, 100, 100], [1000, 1000, 1000]])
    with NumpyIndexer(
        metric='euclidean', ref_indexer=indexer, metas=test_metas
    ) as new_indexer:
        assert new_indexer.compress_level == compress_level
        assert new_indexer.index_filename == index_filename
        assert isinstance(indexer, NumpyIndexer)
        if compress_level == 0:
            assert isinstance(new_indexer.query_handler, np.memmap)
        idx, dist = new_indexer.query(queries, top_k=2)
        np.testing.assert_equal(
            idx, np.array([['4', '5'], ['5', '4'], ['6', '5'], ['7', '6']])
        )
        assert idx.shape == dist.shape
        assert idx.shape == (4, 2)
        np.testing.assert_equal(new_indexer.query_by_key(['7', '4']), vectors[[3, 0]])
