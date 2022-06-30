from docarray import Document, DocumentArray

from jina import Executor, requests


class TestExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, parameters, **kwargs):
        assert docs is not None
        assert parameters is not None
