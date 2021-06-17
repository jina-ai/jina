from jina import Executor, requests

from dep import hello


class MyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @requests
    def foo(self, **kwargs):
        hello()
