from jina import Executor, requests, DocumentArray

from .helper import print_something


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text *= 2
        print_something()
