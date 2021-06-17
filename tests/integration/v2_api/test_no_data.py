from jina import requests, Flow, DocumentArray
from jina.executors import BaseExecutor


class MockExecutor(BaseExecutor):
    @requests
    def encode(self, docs, **kwargs):
        assert len(docs) == 0


def test_empty_documents():
    with Flow().add(uses=MockExecutor) as f:
        results = f.post(on='/test', inputs=[], return_results=True)
        assert results[0].status.code == 0  # SUCCESS


def test_no_documents():
    with Flow().add(uses=MockExecutor) as f:
        results = f.post(on='/test', inputs=None, return_results=True)
        assert results[0].status.code == 0  # SUCCESS
