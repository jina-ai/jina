from jina import DocumentArray, Executor, requests

from .helper import print_something
from .utils.data import dataops
from .utils.io import ioops


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text *= 2
        ioops()
        dataops()
        print_something()
