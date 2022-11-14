from jina import DocumentArray, Executor, requests


class SimpleIndexerTracing(Executor):
    """"""

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        pass
