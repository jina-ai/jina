from jina import Executor, requests, DocumentArray


class TestExecutor(Executor):
    @requests
    def process(self, docs: DocumentArray, **kwargs):
        return docs
