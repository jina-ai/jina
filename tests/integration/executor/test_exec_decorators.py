import pytest

from jina import Executor, dynamic_batching, requests


@pytest.mark.parametrize(
    'inputs,expected_values',
    [
        (
            dict(preferred_batch_size=4, timeout=5_000, max_batch_size=256),
            dict(preferred_batch_size=4, timeout=5_000, max_batch_size=256),
        ),
        (
            dict(preferred_batch_size=4, timeout=5_000),
            dict(preferred_batch_size=4, timeout=5_000, max_batch_size=None),
        ),
        (
            dict(preferred_batch_size=4, max_batch_size=256),
            dict(preferred_batch_size=4, timeout=10_000, max_batch_size=256),
        ),
    ],
)
def test_dynamic_batching(inputs, expected_values):
    class MyExec(Executor):
        @dynamic_batching(**inputs)
        def foo(self, docs, **kwargs):
            pass

    exec = MyExec()
    assert exec.dynamic_batching['foo'] == expected_values


@pytest.mark.parametrize(
    'inputs,expected_values',
    [
        (
            dict(preferred_batch_size=4, timeout=5_000, max_batch_size=256),
            dict(preferred_batch_size=4, timeout=5_000, max_batch_size=256),
        ),
        (
            dict(preferred_batch_size=4, timeout=5_000),
            dict(preferred_batch_size=4, timeout=5_000, max_batch_size=None),
        ),
        (
            dict(preferred_batch_size=4, max_batch_size=256),
            dict(preferred_batch_size=4, timeout=10_000, max_batch_size=256),
        ),
    ],
)
def test_combined_decorators(inputs, expected_values):
    class MyExec(Executor):
        @dynamic_batching(**inputs)
        @requests(on='/foo')
        def foo(self, docs, **kwargs):
            pass

    exec = MyExec()
    assert exec.dynamic_batching['foo'] == expected_values

    class MyExec(Executor):
        @requests(on='/foo')
        @dynamic_batching(**inputs)
        def foo(self, docs, **kwargs):
            pass

    exec = MyExec()
    assert exec.dynamic_batching['foo'] == expected_values
