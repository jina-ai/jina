from jina import requests, Flow
from jina.executors import BaseExecutor


class MockExecutorEmpty(BaseExecutor):
    @requests
    def encode(self, docs, **kwargs):
        assert docs == []


class MockExecutorNone(BaseExecutor):
    @requests
    def encode(self, docs, **kwargs):
        assert docs is None


def test_empty_documents():
    with Flow().add(uses=MockExecutorEmpty) as f:
        results = f.post(on='/test', inputs=[], return_results=True)
        assert results[0].status.code == 0  # SUCCESS


def test_no_documents():
    with Flow().add(uses=MockExecutorNone) as f:
        results = f.post(on='/test', inputs=None, return_results=True)
        assert results[0].status.code == 0  # SUCCESS
