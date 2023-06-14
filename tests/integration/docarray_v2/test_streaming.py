from typing import Optional

import pytest

from jina import Client, Executor, requests
from jina._docarray import Document, DocumentArray
from jina.helper import random_port


class MyDocument(Document):
    text: str
    number: Optional[int]


class MyExecutor(Executor):
    @requests(on='/hello')
    async def task(self, doc: MyDocument, **kwargs):
        for i in range(100):
            yield MyDocument(text=f'{doc.text} {doc.number + i}')


@pytest.mark.asyncio
async def test_streaming_sse_http_deployment():
    from jina import Deployment

    port = random_port()

    with Deployment(
        uses=MyExecutor,
        timeout_ready=-1,
        protocol='http',
        cors=True,
        port=port,
        include_gateway=False,
    ):
        client = Client(port=port, protocol='http', cors=True, asyncio=True)
        i = 10
        async for doc in client.stream_doc(
            on='/hello',
            inputs=MyDocument(text='hello world', number=i),
            return_type=MyDocument,
        ):
            assert doc.text == f'hello world {i}'
            i += 1


class Executor1(Executor):
    @requests
    def generator(self, doc: MyDocument, **kwargs):
        yield MyDocument(text='new document')

    @requests(on='/non_generator')
    def non_generator(self, docs: DocumentArray, **kwargs):
        return docs


class Executor2(Executor):
    @requests
    def non_generator(self, docs: DocumentArray, **kwargs):
        return docs

    @requests(on='/generator')
    def generator(self, doc: MyDocument, **kwargs):
        yield MyDocument(text='new document')


class Executor3(Executor):
    @requests(on='/non_generator')
    def non_generator(self, docs: DocumentArray, **kwargs):
        return docs

    @requests(on='/generator')
    def generator(self, doc: MyDocument, **kwargs):
        yield MyDocument(text='new document')


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
