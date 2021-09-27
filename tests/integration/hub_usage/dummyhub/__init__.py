from jina import Executor

from .helper import foo


class DummyHubExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        foo()
