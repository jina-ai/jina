import asyncio
import time

import pytest

from jina import DocumentArray, Executor, requests, Document, DocumentArrayMemmap
from jina.logging.logger import JinaLogger
from jina.parsers import set_pea_parser
from jina.peapods.runtimes.request_handlers.data_request_handler import (
    DataRequestHandler,
)
from jina.clients.request import request_generator


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


@pytest.fixture()
def logger():
    return JinaLogger('data request handler')


@pytest.mark.asyncio
async def test_data_request_handler_new_docs(logger):
    args = set_pea_parser().parse_args(['--uses', 'NewDocsExecutor'])
    handler = DataRequestHandler(args, logger)
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
async def test_aync_data_request_handler_new_docs(logger):
    args = set_pea_parser().parse_args(['--uses', 'AsyncNewDocsExecutor'])
    handler = DataRequestHandler(args, logger)
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
async def test_data_request_handler_change_docs(logger):
    args = set_pea_parser().parse_args(['--uses', 'ChangeDocsExecutor'])
    handler = DataRequestHandler(args, logger)

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
async def test_data_request_handler_change_docs_dam(logger, tmpdir):
    class MemmapExecutor(Executor):
        @requests
        def foo(self, docs, **kwargs):
            dam = DocumentArrayMemmap(tmpdir + '/dam')
            dam.extend(docs)
            return dam

    args = set_pea_parser().parse_args(['--uses', 'MemmapExecutor'])
    handler = DataRequestHandler(args, logger)

    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    assert len(req.docs) == 10
    response = await handler.handle(requests=[req])

    assert len(response.docs) == 10
    for doc in response.docs:
        assert doc.text == 'input document'


@pytest.mark.asyncio
async def test_data_request_handler_change_docs_from_partial_requests(logger):
    NUM_PARTIAL_REQUESTS = 5
    args = set_pea_parser().parse_args(['--uses', 'MergeChangeDocsExecutor'])
    handler = DataRequestHandler(args, logger)

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
