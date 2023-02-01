import os

from jina import Executor, requests


class DummyExecutor(Executor):
    def __init__(self, arg='hello', **kwargs):
        super().__init__(**kwargs)
        self.arg = arg

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = self.arg
