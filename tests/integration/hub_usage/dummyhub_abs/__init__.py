from helper import foo

from jina.executors.crafters import BaseCrafter


class DummyHubExecutorAbs(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        foo()
