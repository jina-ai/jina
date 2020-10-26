import os

import numpy as np
import pytest

from jina.executors.decorators import as_update_method, as_train_method, as_ndarray, batching, \
    require_train, store_init_kwargs, batching_multi_input

cur_dir = os.path.dirname(os.path.abspath(__file__))


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


@pytest.mark.skip(reason='Currently wrong implementation of batching with labels, not well considered in batching helper')
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
    class A:
        def __init__(self, batch_size):
            self.batch_size = batch_size
            self.batching0 = []
            self.batching1 = []
            self.batching2 = []

        @batching_multi_input(args_indeces=(1, 3))
        def f(self, datas):
            assert len(datas) == 3
            self.batching0.append(datas[0])
            self.batching1.append(datas[1])
            self.batching2.append(datas[2])
            return [datas[0], datas[1], datas[2]]

    instance = A(2)
    data = [np.random.rand(4, 2), np.random.rand(4, 4), np.random.rand(4, 6)]
    print(data)
    print(f'len {len(data)}')
    print(f'data0 {data[0]}')
    result = instance.f(data)
    assert len(instance.batching0) == 2
    assert len(instance.batching1) == 2
    assert len(instance.batching0[0]) == 2
    assert len(instance.batching0[1]) == 2
    assert len(instance.batching1[0]) == 2
    assert len(instance.batching1[1]) == 2

