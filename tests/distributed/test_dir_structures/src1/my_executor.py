from jina.types.arrays.document import DocumentArray
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text *= 2
