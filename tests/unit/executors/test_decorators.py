import os

import numpy as np
import pytest

from jina.executors.decorators import as_update_method, as_train_method, as_ndarray, batching, \
    require_train, store_init_kwargs, batching_multi_input


def test_as_update_method():
    class A:
        def __init__(self):
            self.is_updated = False

        @as_update_method
        def f(self):
            pass

    a = A()
    assert not a.is_updated
    a.f()
    assert a.is_updated


def test_as_train_method():
    class A:
        def __init__(self):
            self.is_trained = False

        @as_train_method
        def f(self):
            pass

    a = A()
    assert not a.is_trained
    a.f()
    assert a.is_trained


def test_as_ndarray():
    class A:
        @as_ndarray
        def f_list(self, *args, **kwargs):
            return [0]

        @as_ndarray
        def f_int(self, *args, **kwargs):
            return 0

    a = A()

    assert isinstance(a.f_list(), np.ndarray)
    with pytest.raises(TypeError):
        a.f_int()


def test_require_train():
    class A:
        def __init__(self):
            self.is_trained = False

        @require_train
        def f(self):
            pass

    a = A()
    a.is_trained = False
    with pytest.raises(RuntimeError):
        a.f()
    a.is_trained = True
    a.f()


def test_store_init_kwargs():
    class A:
        @store_init_kwargs
        def __init__(self, a, b, c, *args, **kwargs):
            pass

        @store_init_kwargs
        def f(self, a, b, *args, **kwargs):
            pass

    instance = A('a', 'b', c=5, d='d')
    assert instance._init_kwargs_dict
    assert instance._init_kwargs_dict == {'a': 'a', 'b': 'b', 'c': 5}

    with pytest.raises(TypeError):
        instance.f('a', 'b', c='c')


def test_batching():
    class A:
        def __init__(self, batch_size):
            self.batch_size = batch_size
            self.batch_sizes = []

        @batching
        def f(self, data):
            self.batch_sizes.append(len(data))
            return data

    instance = A(1)
    result = instance.f([1, 1, 1, 1])
    assert result == [[1], [1], [1], [1]]
    assert len(instance.batch_sizes) == 4
    for batch_size in instance.batch_sizes:
        assert batch_size == 1

    instance = A(3)
    result = instance.f([1, 1, 1, 1])
    assert result == [[1, 1, 1], [1]]
    assert len(instance.batch_sizes) == 2
    assert instance.batch_sizes[0] == 3
    assert instance.batch_sizes[1] == 1

    instance = A(5)
    result = instance.f([1, 1, 1, 1])
    assert result == [1, 1, 1, 1]
    assert len(instance.batch_sizes) == 1
    assert instance.batch_sizes[0] == 4


def test_batching_slice_on():
    class A:
        def __init__(self, batch_size):
            self.batch_size = batch_size
            self.batch_sizes = []

        @batching(slice_on=2)
        def f(self, key, data):
            self.batch_sizes.append(len(data))
            return data

    instance = A(1)
    result = instance.f(None, [1, 1, 1, 1])
    assert result == [[1], [1], [1], [1]]
    assert len(instance.batch_sizes) == 4
    for batch_size in instance.batch_sizes:
        assert batch_size == 1

    instance = A(3)
    result = instance.f(None, [1, 1, 1, 1])
    assert result == [[1, 1, 1], [1]]
    assert len(instance.batch_sizes) == 2
    assert instance.batch_sizes[0] == 3
    assert instance.batch_sizes[1] == 1

    instance = A(5)
    result = instance.f(None, [1, 1, 1, 1])
    assert result == [1, 1, 1, 1]
    assert len(instance.batch_sizes) == 1
    assert instance.batch_sizes[0] == 4


def test_batching_ordinal_idx_arg(tmpdir):
    path = os.path.join(str(tmpdir), 'vec.gz')
    vec = np.random.random([10, 10])
    with open(path, 'wb') as f:
        f.write(vec.tobytes())

    class A:
        def __init__(self, batch_size):
            self.batch_size = batch_size
            self.ord_idx = []

        @batching(ordinal_idx_arg=2)
        def f(self, data, ord_idx):
            self.ord_idx.append(ord_idx)
            return list(range(ord_idx.start, ord_idx.stop))

    instance = A(2)
    result = instance.f(np.memmap(path, dtype=vec.dtype.name, mode='r', shape=vec.shape), vec.shape[0])
    assert len(instance.ord_idx) == 5
    assert instance.ord_idx[0].start == 0
    assert instance.ord_idx[0].stop == 2
    assert instance.ord_idx[1].start == 2
    assert instance.ord_idx[1].stop == 4
    assert instance.ord_idx[2].start == 4
    assert instance.ord_idx[2].stop == 6
    assert instance.ord_idx[3].start == 6
    assert instance.ord_idx[3].stop == 8
    assert instance.ord_idx[4].start == 8
    assert instance.ord_idx[4].stop == 10

    assert result == [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]


@pytest.mark.skip(
    reason='Currently wrong implementation of batching with labels, not well considered in batching helper')
def test_batching_with_label():
    class A:
        def __init__(self, batch_size):
            self.batch_size = batch_size

        @batching(label_on=2)
        def f(self, data, labels):
            return data, labels

    instance = A(2)
    data = [1, 1, 2, 2]
    labels = ['label1', 'label1', 'label2', 'label2']
    result = instance.f(data, labels)
    assert result == [[(1, 'label1'), (1, 'label1')], [(2, 'label2'), (2, 'label2')]]


def test_batching_multi():
    num_data = 3

    class A:
        def __init__(self, batch_size):
            self.batch_size = batch_size
            self.batching = []

        @batching_multi_input(num_data=num_data)
        def f(self, *datas):
            assert len(datas) == num_data
            concat = np.concatenate(datas, axis=1)
            self.batching.append(concat)
            return concat

    num_docs = 4
    batch_size = 2
    instance = A(batch_size)
    data0 = np.random.rand(num_docs, 2)
    data1 = np.random.rand(num_docs, 4)
    data2 = np.random.rand(num_docs, 6)
    data = [data0, data1, data2]
    result = instance.f(*data)
    from math import ceil
    result_dim = sum([d.shape[1] for d in data])
    assert result.shape == (num_docs, result_dim)
    assert len(instance.batching) == ceil(num_docs / batch_size)
    for batch in instance.batching:
        assert batch.shape == (batch_size, result_dim)

def test_batching_multi_input_dictionary():
    batch_size = 2
    class MockRanker:
        def __init__(self, batch_size):
            self.batch_size=batch_size
            self.batches = []

        @batching_multi_input(slice_on=2,num_data=2)
        def score(
            self, query_meta, old_match_scores, match_meta
        ):
            self.batches.append([query_meta, old_match_scores, match_meta])
            return np.array([(x,y) for x,y in old_match_scores.items()])
    
    query_meta = {'text': 'cool stuff'}
    old_match_scores = {1: 5, 2: 4, 3:4 , 4:0}
    match_meta = {1: {'text': 'cool stuff'}, 2: {'text': 'kewl stuff'},3: {'text': 'kewl stuff'},4: {'text': 'kewl stuff'}}
    instance = MockRanker(batch_size)
    result = instance.score(query_meta,old_match_scores,match_meta)
    np.testing.assert_almost_equal(result,np.array([(x,y) for x,y in old_match_scores.items()]))
    for batch in instance.batches:
        assert batch[0] == query_meta
        assert len(batch[1]) == batch_size
        assert len(batch[2]) == batch_size

