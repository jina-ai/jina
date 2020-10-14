import os

import numpy as np
import pytest

from jina.executors.decorators import (
    as_update_method,
    as_train_method,
    as_ndarray,
    batching,
    require_train,
    store_init_kwargs,
)

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

    instance = A("a", "b", c=5, d="d")
    assert instance._init_kwargs_dict
    assert instance._init_kwargs_dict == {"a": "a", "b": "b", "c": 5}

    with pytest.raises(TypeError):
        instance.f("a", "b", c="c")


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
