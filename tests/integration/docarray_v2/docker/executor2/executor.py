from typing import Optional, List
from docarray import DocList, BaseDoc
from docarray.typing import NdArray
from docarray.index import InMemoryExactNNIndex
from jina import Executor, requests


class MyDoc(BaseDoc):
    text: str
    embedding: Optional[NdArray] = None


class MyDocWithMatches(MyDoc):
    matches: DocList[MyDoc] = []
    scores: List[float] = []


class Indexer(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._indexer = InMemoryExactNNIndex[MyDoc]()

    @requests(on='/index')
    def index(self, docs: DocList[MyDoc], **kwargs) -> DocList[MyDoc]:
        self._indexer.index(docs)
        return docs

    @requests(on='/search')
    def search(self, docs: DocList[MyDoc], **kwargs) -> DocList[MyDocWithMatches]:
        res = DocList[MyDocWithMatches]()
        ret = self._indexer.find_batched(docs, search_field='embedding')
        matched_documents = ret.documents
        matched_scores = ret.scores
        for query, matches, scores in zip(docs, matched_documents, matched_scores):
            output_doc = MyDocWithMatches(**query.dict())
            output_doc.matches = matches
            output_doc.scores = scores.tolist()
            res.append(output_doc)
        return res
