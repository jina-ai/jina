import time

from jina import Executor, requests


class NoopExecutor(Executor):
    @requests
    def index(self, docs, **kwargs):
        docs[0].text = f'{time.time()}'
        return docs
