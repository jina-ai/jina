import pytest
from docarray import Document, DocumentArray

from jina import Executor, requests
from jina.clients.request import request_generator
from jina.logging.logger import JinaLogger
from jina.parsers import set_pod_parser
from jina.serve.runtimes.request_handlers.data_request_handler import DataRequestHandler


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
async def test_data_request_handler_new_docs(logger):
    args = set_pod_parser().parse_args(['--uses', 'NewDocsExecutor'])
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
    args = set_pod_parser().parse_args(['--uses', 'AsyncNewDocsExecutor'])
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
    args = set_pod_parser().parse_args(['--uses', 'ChangeDocsExecutor'])
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
async def test_data_request_handler_change_docs_from_partial_requests(logger):
    NUM_PARTIAL_REQUESTS = 5
    args = set_pod_parser().parse_args(['--uses', 'MergeChangeDocsExecutor'])
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


@pytest.mark.asyncio
async def test_data_request_handler_clear_docs(logger):
    args = set_pod_parser().parse_args(['--uses', 'ClearDocsExecutor'])
    handler = DataRequestHandler(args, logger)

    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    assert len(req.docs) == 10
    response = await handler.handle(requests=[req])

    assert len(response.docs) == 0


@pytest.mark.parametrize(
    'key_name,is_specific',
    [
        ('key', False),
        ('key_1', False),
        ('executor__key', True),
        ('exec2__key_2', True),
        ('__results__', False),
    ],
)
def test_is_specific_executor(key_name, is_specific):
    assert DataRequestHandler._is_param_for_specific_executor(key_name) == is_specific


@pytest.mark.parametrize(
    'full_key,key , executor',
    [
        ('executor__key', 'key', 'executor'),
        ('executor__key_1', 'key_1', 'executor'),
        ('executor_1__key', 'key', 'executor_1'),
    ],
)
def test_split_key_executor_name(full_key, key, executor):
    assert DataRequestHandler._spit_key_and_executor_name(full_key) == (key, executor)


@pytest.mark.parametrize(
    'param, parsed_param, executor_name',
    [
        (
            {'key': 1, 'executor__key': 2, 'wrong_executor__key': 3},
            {'key': 2},
            'executor',
        ),
        ({'executor__key': 2, 'wrong_executor__key': 3}, {'key': 2}, 'executor'),
        (
            {'a': 1, 'executor__key': 2, 'wrong_executor__key': 3},
            {'key': 2, 'a': 1},
            'executor',
        ),
        ({'key_1': 0, 'exec2__key_2': 1}, {'key_1': 0}, 'executor'),
    ],
)
def test_parse_specific_param(param, parsed_param, executor_name):
    assert (
        DataRequestHandler._parse_specific_params(param, executor_name) == parsed_param
    )


@pytest.mark.parametrize(
    'name_w_replicas,name', [('exec1/rep-0', 'exec1'), ('exec1', 'exec1')]
)
def test_get_name_from_replicas(name_w_replicas, name):
    assert DataRequestHandler._get_name_from_replicas_name(name_w_replicas) == name
