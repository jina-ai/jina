import pytest
from collections import OrderedDict
from jina import Document, DocumentArray, Executor, Flow, requests


@pytest.mark.timeout(5)
@pytest.mark.parametrize('replicas_shards', [(1, 1), (2, 2)])
def test_sharding_tail_pea(replicas_shards):
    """TODO(Maximilian): Make (1, 2) and (2, 1) also workable"""
    num_shards, num_replicas = replicas_shards

    class DummyExecutor(Executor):
        @requests
        def do_something(self, docs, **kwargs):
            print('Hello World!')

    class MatchMerger(Executor):
        @requests
        def merge(self, docs_matrix, **kwargs):
            results = OrderedDict()
            for docs in docs_matrix:
                for doc in docs:
                    if doc.id in results:
                        results[doc.id].matches.extend(doc.matches)
                    else:
                        results[doc.id] = doc
            return DocumentArray(results.values())

    f = Flow().add(
        uses=DummyExecutor,
        replicas=num_replicas,
        shards=num_shards,
        uses_after=MatchMerger,
    )
    with f:
        results = f.post(
            on='/search',
            inputs=Document(matches=[Document()]),
            return_results=True,
        )
        assert len(results[0].docs[0].matches) == num_shards
