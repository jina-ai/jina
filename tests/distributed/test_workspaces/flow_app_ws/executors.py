import numpy as np
from tinydb import TinyDB, where
from sklearn.utils import shuffle
from docarray import Document, DocumentArray
from jina import requests, Executor


class TinyDBIndexer(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = TinyDB('db.json')

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self.db.insert_multiple(docs[:, 'tags'])

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            r = self.db.search(where(doc.tags['key']) == doc.tags['value'])
            if len(r) > 0:
                doc.matches = DocumentArray()
                doc.matches.append(Document(tags=r[0]))


class SklearnExecutor(Executor):
    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        """This just validates sklearn is installed in the workspace"""
        for doc in docs:
            doc.embedding = shuffle(np.random.rand(2, 3))
