from jina import Executor, requests


class MyExecutor(Executor):
    def __init__(self, bar, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar

    @requests
    def process(self, docs, **kwargs):
        for d in docs:
            d.text = 'hello world'
        return docs
