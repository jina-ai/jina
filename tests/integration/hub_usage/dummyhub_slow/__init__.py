import time

from jina import Executor
from .helper import foo


class DummyHubExecutorSlow(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        time.sleep(15)
        foo()
