from jina import Executor
from .helper import foo


class DummyHubExecutorAbs(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        foo()
