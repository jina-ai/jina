import time

from jina import Executor, requests, DocumentArray


class MyDummyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._docs = DocumentArray()

    @requests(on='/index')
    def index(self, docs, **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def search(self, docs, **kwargs):
        # The executor needs to do change some state to avoid cheese caching tricks to work
        self._docs[0].text = f'{time.time()}'
        return self._docs
