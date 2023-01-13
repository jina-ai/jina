import os

from jina import Executor, requests


class DummyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        pass
