from jina import DocumentArray, Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text *= 2
