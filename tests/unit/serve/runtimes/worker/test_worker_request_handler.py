import pytest

from docarray import Document, DocumentArray
from jina import Executor, requests
from jina.clients.request import request_generator
from jina.logging.logger import JinaLogger
from jina.parsers import set_pod_parser
from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler


class NewDocsExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        return DocumentArray([Document(text='new document')])


class AsyncNewDocsExecutor(Executor):
    @requests
    async def foo(self, docs, **kwargs):
        return DocumentArray([Document(text='new document')])


class ChangeDocsExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'changed document'


class MergeChangeDocsExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'changed document'
        return docs


class ClearDocsExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        docs.clear()


@pytest.fixture()
def logger():
    return JinaLogger('data request handler')


@pytest.mark.asyncio
async def test_worker_request_handler_new_docs(logger):
    args = set_pod_parser().parse_args(['--uses', 'NewDocsExecutor'])
    handler = WorkerRequestHandler(args, logger)
    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    assert len(req.docs) == 10
    response = await handler.handle(requests=[req])

    assert len(response.docs) == 1
    assert response.docs[0].text == 'new document'


@pytest.mark.asyncio
async def test_aync_worker_request_handler_new_docs(logger):
    args = set_pod_parser().parse_args(['--uses', 'AsyncNewDocsExecutor'])
    handler = WorkerRequestHandler(args, logger)
    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    assert len(req.docs) == 10
    response = await handler.handle(requests=[req])

    assert len(response.docs) == 1
    assert response.docs[0].text == 'new document'


@pytest.mark.asyncio
async def test_worker_request_handler_change_docs(logger):
    args = set_pod_parser().parse_args(['--uses', 'ChangeDocsExecutor'])
    handler = WorkerRequestHandler(args, logger)

    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    assert len(req.docs) == 10
    response = await handler.handle(requests=[req])

    assert len(response.docs) == 10
    for doc in response.docs:
        assert doc.text == 'changed document'


@pytest.mark.asyncio
async def test_worker_request_handler_change_docs_from_partial_requests(logger):
    NUM_PARTIAL_REQUESTS = 5
    args = set_pod_parser().parse_args(['--uses', 'MergeChangeDocsExecutor'])
    handler = WorkerRequestHandler(args, logger)

    partial_reqs = [
        list(
            request_generator(
                '/', DocumentArray([Document(text='input document') for _ in range(10)])
            )
        )[0]
    ] * NUM_PARTIAL_REQUESTS
    assert len(partial_reqs) == 5
    assert len(partial_reqs[0].docs) == 10
    response = await handler.handle(requests=partial_reqs)

    assert len(response.docs) == 10 * NUM_PARTIAL_REQUESTS
    for doc in response.docs:
        assert doc.text == 'changed document'


@pytest.mark.asyncio
async def test_worker_request_handler_clear_docs(logger):
    args = set_pod_parser().parse_args(['--uses', 'ClearDocsExecutor'])
    handler = WorkerRequestHandler(args, logger)

    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    assert len(req.docs) == 10
    response = await handler.handle(requests=[req])

    assert len(response.docs) == 0
