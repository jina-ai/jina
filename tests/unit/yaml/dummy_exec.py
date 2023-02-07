from docarray import DocumentArray

from jina import requests
from jina.serve.executors import BaseExecutor


class DummyExternalIndexer(BaseExecutor):
    @requests
    def index(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.text = 'indexed'
