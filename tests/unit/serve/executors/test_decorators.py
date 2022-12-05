import functools

import pytest

from jina.helper import iscoroutinefunction
from jina.serve.executors import get_executor_taboo
from jina.serve.executors.decorators import dynamic_batching, requests
from jina.serve.helper import store_init_kwargs


def test_store_init_kwargs():
    store_init_kwargs_decorator = functools.partial(
        store_init_kwargs, taboo=get_executor_taboo()
    )

    class A:
        @store_init_kwargs_decorator
        def __init__(self, a, b, c, *args, **kwargs):
            pass

        @store_init_kwargs_decorator
        def f(self, a, b, *args, **kwargs):
            pass

    instance = A('a', 'b', c=5, d='d')
    assert instance._init_kwargs_dict
    assert instance._init_kwargs_dict == {'a': 'a', 'b': 'b', 'c': 5}

    with pytest.raises(TypeError):
        instance.f('a', 'b', c='c')


def test_requests():
    with pytest.raises(TypeError):

        @requests
        def fn(*args):
            pass

    @requests
    def fn_2(*args, **kwargs):
        pass

    assert hasattr(fn_2, 'fn')


def test_async_requests():
    with pytest.raises(TypeError):

        @requests
        def fn(*args):
            pass

    @requests
    def fn_2(*args, **kwargs):
        pass

    @requests
    async def fn_3(*args, **kwargs):
        pass

    assert hasattr(fn_2, 'fn')
    assert not iscoroutinefunction(getattr(fn_2, 'fn'))
    assert hasattr(fn_3, 'fn')
    assert iscoroutinefunction(getattr(fn_3, 'fn'))


def test_dynamic_batching():
    @dynamic_batching()
    def fn_2(*args, **kwargs):
        pass

    assert hasattr(fn_2, 'fn')


def test_async_dynamic_batching():
    @dynamic_batching
    def fn_2(*args, **kwargs):
        pass

    @dynamic_batching
    async def fn_3(*args, **kwargs):
        pass

    assert hasattr(fn_2, 'fn')
    assert not iscoroutinefunction(getattr(fn_2, 'fn'))
    assert hasattr(fn_3, 'fn')
    assert iscoroutinefunction(getattr(fn_3, 'fn'))
