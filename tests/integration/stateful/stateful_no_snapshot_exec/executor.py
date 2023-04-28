from jina import DocumentArray, Executor, requests
from jina.serve.executors.decorators import write
import random
import os

from typing import Dict, List

from docarray.documents import TextDoc


class TextDocWithId(TextDoc):
    id: str
    tags: Dict[str, str] = {}
    l: List[str] = []


random_num = random.randint(0, 50000)


class MyStateExecutorNoSnapshot(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArray[TextDocWithId]()
        self._docs_dict = {}
        self.logger.warning(f'RANDOM NUM {random_num}')

    @requests(on=['/index'])
    @write
    def index(self, docs: DocumentArray[TextDocWithId], **kwargs):
        for doc in docs:
            self.logger.debug(f'Indexing doc {doc.text} with ID {doc.id}')
            self._docs.append(doc)
            self._docs_dict[doc.id] = doc

    @requests(on=['/search'])
    def search(self, docs: DocumentArray[TextDocWithId], **kwargs):
        for doc in docs:
            self.logger.debug(f'Searching against {len(self._docs)} documents')
            doc.text = self._docs_dict[doc.id].text
            doc.tags['pid'] = os.getpid()
            doc.tags['num'] = random_num

    @requests(on=['/similarity'])
    def search_similarity(self, docs: DocumentArray[TextDocWithId], **kwargs):
        for doc in docs:
            self.logger.debug(f'Searching similarity against {len(self._docs)} documents')
            doc.text = 'similarity'
            doc.l = [doc.id for doc in self._docs]
