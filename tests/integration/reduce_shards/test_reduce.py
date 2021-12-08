from typing import Dict

import pytest

from jina import Document, DocumentArray, Flow, Executor, requests


class MyExecutor(Executor):
    def __init__(self, n_docs: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.n_docs = n_docs

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.matches.extend(
                [
                    Document(id=f'm-{self.runtime_args.pea_id}-{i}')
                    for i in range(self.n_docs)
                ]
            )
            doc.chunks.extend(
                [
                    Document(id=f'c-{self.runtime_args.pea_id}-{i}')
                    for i in range(self.n_docs)
                ]
            )


@pytest.mark.parametrize('n_shards', [3, 5])
@pytest.mark.parametrize('n_docs', [3, 5])
def test_reduce_shards(n_shards, n_docs):
    search_flow = Flow().add(
        uses=MyExecutor,
        shards=n_shards,
        polling='all',
        uses_with={'n_docs': n_docs},
    )

    with search_flow as f:
        da = DocumentArray([Document() for _ in range(5)])
        resp = f.post('/search', inputs=da, return_results=True)

    for doc in resp[0].docs:
        matches = set([doc.id for doc in doc.matches])
        chunks = set([doc.id for doc in doc.chunks])
        for shard in range(n_shards):
            for match in range(n_docs):
                assert f'm-{shard}-{match}' in matches
            for chunk in range(n_docs):
                assert f'c-{shard}-{chunk}' in chunks


@pytest.mark.parametrize('n_shards', [3, 5])
@pytest.mark.parametrize('n_docs', [3, 5])
def test_uses_after_no_reduce(n_shards, n_docs):
    search_flow = Flow().add(
        uses=MyExecutor,
        shards=n_shards,
        uses_after='Executor',
        polling='all',
        uses_with={'n_docs': n_docs},
    )

    with search_flow as f:
        da = DocumentArray([Document() for _ in range(5)])
        resp = f.post('/search', inputs=da, return_results=True)

    for doc in resp[0].docs:
        matches = set([doc.id for doc in doc.matches])
        chunks = set([doc.id for doc in doc.chunks])
        for shard in range(n_shards):
            for match in range(n_docs):
                assert f'm-{shard}-{match}' in matches
            for chunk in range(n_docs):
                assert f'c-{shard}-{chunk}' in chunks
