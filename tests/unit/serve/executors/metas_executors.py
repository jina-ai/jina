from jina import DocumentArray, Executor, requests


class TestExecutor(Executor):
    @requests
    def process(self, docs: DocumentArray, **kwargs):
        return docs
