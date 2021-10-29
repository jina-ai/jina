from jina import Executor, requests, DocumentArray

from .utils.io import ioops
from .utils.data import dataops
from .helper import print_something


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        import tinydb
        import sklearn

        assert tinydb, sklearn

        docs[0].text *= 2
        ioops()
        dataops()
        print_something()
