import numpy as np
from jina import Document, DocumentArray, Executor, Flow, requests

class CharEmbed(Executor):  # a simple character embedding with mean-pooling
    offset = 32  # letter `a`
    dim = 127 - offset + 1  # last pos reserved for `UNK`
    char_embd = np.eye(dim) * 1  # one-hot embedding for all chars

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for d in docs:
            r_emb = [ord(c) - self.offset if self.offset <= ord(c) <= 127 else (self.dim - 1) for c in d.text]
            d.embedding = self.char_embd[r_emb, :].mean(axis=0)  # average pooling

class Indexer(Executor):
    _docs = DocumentArray()  # for storing all documents in memory

    @requests(on='/index')
    def foo(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)  # extend stored `docs`

    @requests(on='/search')
    def bar(self, docs: DocumentArray, **kwargs):
        q = np.stack(docs.get_attributes('embedding'))  # get all embeddings from query docs
        d = np.stack(self._docs.get_attributes('embedding'))  # get all embeddings from stored docs
        euclidean_dist = np.linalg.norm(q[:, None, :] - d[None, :, :], axis=-1)  # pairwise euclidean distance
        for dist, query in zip(euclidean_dist, docs):  # add & sort match
            query.matches = [Document(self._docs[int(idx)], copy=True, scores={'euclid': d}) for idx, d in enumerate(dist)]
            query.matches.sort(key=lambda m: m.scores['euclid'].value)  # sort matches by their values

f = Flow(port_expose=12345, protocol='http').add(uses=CharEmbed, parallel=2).add(uses=Indexer)  # build a Flow, with 2 parallel CharEmbed, tho unnecessary
with f:
    f.post('/index', (Document(text=t.strip()) for t in open(__file__) if t.strip()))  # index all lines of _this_ file
    f.block()  # block for listening request

