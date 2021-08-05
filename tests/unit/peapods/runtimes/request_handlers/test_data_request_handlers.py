import pytest

from jina import DocumentArray, Executor, requests, Document
from jina.logging.logger import JinaLogger
from jina.parsers import set_pea_parser
from jina.types.message import Message
from jina.peapods.runtimes.request_handlers.data_request_handler import (
    DataRequestHandler,
)
from jina.clients.request import request_generator


class NewDocsExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        return DocumentArray([Document(text='new document')])


class ChangeDocsExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'changed document'


@pytest.fixture()
def logger():
    return JinaLogger('data request handler')


def test_data_request_handler_new_docs(logger):
    args = set_pea_parser().parse_args(['--uses', 'NewDocsExecutor'])
    handler = DataRequestHandler(args, logger)
    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    msg = Message(None, req, 'test', '123')
    assert len(msg.request.docs) == 10
    handler.handle(
        msg=msg,
        expected_parts=1,
        partial_requests=None,
        peapod_name='name',
    )

    assert len(msg.request.docs) == 1
    assert msg.request.docs[0].text == 'new document'


def test_data_request_handler_change_docs(logger):
    args = set_pea_parser().parse_args(['--uses', 'ChangeDocsExecutor'])
    handler = DataRequestHandler(args, logger)

    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    msg = Message(None, req, 'test', '123')
    assert len(msg.request.docs) == 10
    handler.handle(
        msg=msg,
        expected_parts=1,
        partial_requests=None,
        peapod_name='name',
    )

    assert len(msg.request.docs) == 10
    for doc in msg.request.docs:
        assert doc.text == 'changed document'
