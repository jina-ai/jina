import os

from jina import Executor, requests


class DummyExec(Executor):
    @requests
    def foo(self, **kwargs):
        pass
