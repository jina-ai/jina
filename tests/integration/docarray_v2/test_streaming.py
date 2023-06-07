from typing import Optional

import pytest

from jina import Client, Executor, requests
from jina._docarray import Document
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
