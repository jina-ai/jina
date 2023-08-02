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
@pytest.mark.parametrize('include_gateway', [False, True])
async def test_streaming_deployment(protocol, include_gateway):
    from jina import Deployment

    port = random_port()

    with Deployment(
        uses=MyExecutor,
        timeout_ready=-1,
        protocol=protocol,
        cors=True,
        port=port,
        include_gateway=include_gateway,
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
