import time

from jina import Executor, Flow, requests


def test_long_executor():
    class LongExecutor(Executor):
        def __init__(self, *arg, **kwargs):
            time.sleep(120)

        @requests()
        def foo(self, *args, **kwargs):
            ...

    with Flow().add(uses=LongExecutor):
        ...
