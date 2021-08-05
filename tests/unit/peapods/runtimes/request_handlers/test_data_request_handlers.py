import pytest

from jina import DocumentArray, Executor, requests, Document
from jina.logging.logger import JinaLogger
from jina.parsers import set_pea_parser
from jina.peapods.runtimes.request_handlers.data_request_handler import (
    DataRequestHandler,
)


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

    docs = DocumentArray([Document(text='input document') for _ in range(10)])
    assert len(docs) == 10
    handler.handle(
        parameters={},
        docs=docs,
        docs_matrix=None,
        groundtruths=None,
        groundtruths_matrix=None,
        exec_endpoint='/search',
        target_peapod='name',
        peapod_name='name',
    )

    assert len(docs) == 1
    assert docs[0].text == 'new document'


def test_data_request_handler_change_docs(logger):
    args = set_pea_parser().parse_args(['--uses', 'ChangeDocsExecutor'])
    handler = DataRequestHandler(args, logger)

    docs = DocumentArray([Document(text='input document') for _ in range(10)])
    assert len(docs) == 10
    handler.handle(
        docs=docs,
        parameters={},
        docs_matrix=None,
        groundtruths=None,
        groundtruths_matrix=None,
        exec_endpoint='/search',
        target_peapod='name',
        peapod_name='name',
    )

    assert len(docs) == 10
    for doc in docs:
        assert doc.text == 'changed document'
