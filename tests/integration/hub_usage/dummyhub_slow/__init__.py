import time
from jina.executors.crafters import BaseCrafter

from .helper import foo


class DummyHubExecutorSlow(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        time.sleep(15)
        foo()
