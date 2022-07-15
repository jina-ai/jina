from jina import DocumentArray, Executor, requests


class TestExecutor(Executor):
    def __init__(self, bar, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar

    @requests
    def process(self, docs: DocumentArray, **kwargs):
        return docs
