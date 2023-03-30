import os

from jina import Deployment, Executor, requests, Flow, Client, DocumentArray, Document


class TestSimpleExecutor(Executor):

    @requests(on='/foo')
    async def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text += f'return foo {os.getpid()}'

    @requests(on='/bar')
    async def bar(self, docs, **kwargs):
        for doc in docs:
            doc.text += f'return bar {os.getpid()}'

    @requests(on='/error')
    async def la(self, docs, **kwargs):
        raise Exception('Raised exception in request')


def test_slow_load_executor():
    pass


def test_fast_executor():
    pass


def test_base_executor():
    pass


def test_replica_pids():
    pass


def test_return_parameters():
    pass


def test_invalid_protocols_with_shards():
    pass
