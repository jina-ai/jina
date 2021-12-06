from typing import Dict

import pytest

from jina import Document, DocumentArray, Flow, Executor, requests


class MyExecutor(Executor):
    def __init__(self, n_matches: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.n_matches = 5

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.matches.extend(
                [
                    Document(id=f'{self.runtime_args.pea_id}-{i}')
                    for i in range(self.n_matches)
                ]
            )


@pytest.mark.parametrize('n_shards', [3, 5])
@pytest.mark.parametrize('n_matches', [3, 5])
def test_reduce_shards(n_shards, n_matches):
    search_flow = Flow().add(
        uses=MyExecutor,
        shards=n_shards,
        polling='all',
        uses_with={'n_matches': n_matches},
    )

    with search_flow as f:
        da = DocumentArray([Document() for _ in range(5)])
        resp = f.post('/search', inputs=da, return_results=True)

    for doc in resp[0].docs:
        matches = set([doc.id for doc in doc.matches])
        for shard in range(n_shards):
            for match in range(n_matches):
                assert f'{shard}-{match}' in matches
