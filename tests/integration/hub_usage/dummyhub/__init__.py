from jina.executors.crafters import BaseCrafter

from .helper import foo


class DummyHubExecutor(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        foo()
