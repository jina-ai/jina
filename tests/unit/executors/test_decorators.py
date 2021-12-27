import pytest

from jina.executors.decorators import store_init_kwargs, requests
from jina.helper import iscoroutinefunction


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
