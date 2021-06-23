from tinydb import TinyDB, where
import torch
from jina import requests, Document, DocumentArray, Executor


class TinyDBIndexer(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = TinyDB('db.json')

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self.db.insert_multiple(docs.get_attributes('tags'))

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            r = self.db.search(where(doc.tags__key) == doc.tags__value)
            if len(r) > 0:
                doc.matches = [Document(tags=r[0])]


class TorchExecutor(Executor):
    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.embedding = torch.rand(2, 3).numpy()
