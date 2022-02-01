import os
from jina import Executor


class EnvChecker(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert os.environ['key1'] == 'value1'
        assert os.environ['key2'] == 'value2'
