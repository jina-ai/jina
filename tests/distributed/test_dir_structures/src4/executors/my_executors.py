from jina import Executor, requests, DocumentArray

from .utils.io import ioops
from .utils.data import dataops
from .helper import print_something


class DataExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text *= 2
        dataops()
        print_something()


class IOExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text *= 2
        ioops()
        print_something()
