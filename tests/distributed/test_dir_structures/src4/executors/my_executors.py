from jina import DocumentArray, Executor, requests

from .helper import print_something
from .utils.data import dataops
from .utils.io import ioops


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
