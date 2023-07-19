import pytest

from jina import Client, Deployment, Executor, requests
from jina._docarray import Document, DocumentArray
from jina.excepts import BadServer
from jina.helper import random_port


class MyExecutor(Executor):
    @requests(on='/hello')
    async def task(self, doc: Document, **kwargs):
        for i in range(100):
            yield Document(text=f'{doc.text} {i}')

    @requests(on='/world')
    async def non_gen_task(self, docs: DocumentArray, **kwargs):
        return docs


@pytest.mark.asyncio
@pytest.mark.parametrize('protocol', ['http', 'grpc'])
async def test_streaming_deployment(protocol):
    from jina import Deployment

    port = random_port()

    with Deployment(
        uses=MyExecutor,
        timeout_ready=-1,
        protocol=protocol,
        cors=True,
        port=port,
        include_gateway=False,
    ):
        client = Client(port=port, protocol=protocol, cors=True, asyncio=True)
        i = 0
        async for doc in client.stream_doc(
            on='/hello', inputs=Document(text='hello world')
        ):
            assert doc.text == f'hello world {i}'
            i += 1


@pytest.mark.asyncio
@pytest.mark.parametrize('protocol', ['grpc'])
async def test_streaming_client_non_gen_endpoint(protocol):
    from jina import Deployment

    port = random_port()

    with Deployment(
        uses=MyExecutor,
        timeout_ready=-1,
        protocol=protocol,
        cors=True,
        port=port,
        include_gateway=False,
    ):
        client = Client(port=port, protocol=protocol, cors=True, asyncio=True)
        i = 0
        with pytest.raises(BadServer):
            async for _ in client.stream_doc(
                on='/world', inputs=Document(text='hello world')
            ):
                pass


def test_invalid_executor():
    with pytest.raises(RuntimeError) as exc_info:

        class InvalidExecutor1(Executor):
            @requests(on='/invalid')
            async def invalid(self, doc: Document, **kwargs):
                return doc

    assert type(exc_info.value.__cause__) is AssertionError

    with pytest.raises(RuntimeError) as exc_info:

        class InvalidExecutor2(Executor):
            @requests(on='/invalid')
            def invalid(self, doc: Document, **kwargs):
                return doc

    assert type(exc_info.value.__cause__) is AssertionError

    with pytest.raises(RuntimeError) as exc_info:

        class InvalidExecutor3(Executor):
            @requests(on='/invalid')
            async def invalid(self, docs: DocumentArray, **kwargs):
                yield docs[0]

    assert type(exc_info.value.__cause__) is AssertionError

    with pytest.raises(RuntimeError) as exc_info:

        class InvalidExecutor4(Executor):
            @requests(on='/invalid')
            def invalid(self, docs: DocumentArray, **kwargs):
                yield docs[0]

    assert type(exc_info.value.__cause__) is AssertionError


class Executor1(Executor):
    @requests
    def generator(self, **kwargs):
        yield Document(text='new document')

    @requests(on='/non_generator')
    def non_generator(self, docs: DocumentArray, **kwargs):
        return docs


class Executor2(Executor):
    @requests
    def non_generator(self, docs: DocumentArray, **kwargs):
        return docs

    @requests(on='/generator')
    def generator(self, **kwargs):
        yield Document(text='new document')


class Executor3(Executor):
    @requests(on='/non_generator')
    def non_generator(self, docs: DocumentArray, **kwargs):
        return docs

    @requests(on='/generator')
    def generator(self, **kwargs):
        yield Document(text='new document')


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'executor,expected',
    [
        ('Executor1', {'/default': True, '/non_generator': False}),
        ('Executor2', {'/default': False, '/generator': True}),
        ('Executor3', {'/generator': True, '/non_generator': False}),
    ],
)
async def test_endpoint_discovery(executor, expected):
    from google.protobuf import json_format

    from jina.logging.logger import JinaLogger
    from jina.parsers import set_pod_parser
    from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler

    args = set_pod_parser().parse_args(['--uses', executor])
    handler = WorkerRequestHandler(args, JinaLogger('data request handler'))
    res = await handler.endpoint_discovery(None, None)
    for endpoint, is_generator in expected.items():
        assert (
            json_format.MessageToDict(res.schemas)[endpoint]['is_generator']
            == is_generator
        )
