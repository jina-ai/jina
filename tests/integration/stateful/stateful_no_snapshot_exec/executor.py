from jina import DocumentArray, Executor, requests
from jina.serve.executors.decorators import write
import random

random_pid = random.randint(0, 50000)


class MyStateExecutorNoSnapshot(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArray()

    @requests(on=['/index'])
    @write
    def index(self, docs, **kwargs):
        for doc in docs:
            self.logger.debug(f' Indexing doc {doc.text}')
            self._docs.append(doc)

    @requests(on=['/search'])
    def search(self, docs, **kwargs):
        for doc in docs:
            doc.text = self._docs[doc.id].text
            doc.tags['pid'] = random_pid
