import pytest
import asyncio

from jina.clients.request.asyncio import request_generator
from jina.enums import RequestType
from math import ceil

from jina import Document

NUM_INPUT_DOCS = 30
REQUEST_SIZE = 10


@pytest.mark.asyncio
async def test_asyncio_req_generator():
    async def input_function():
        data = [Document() for _ in range(NUM_INPUT_DOCS)]
        for doc in data:
            yield doc

    generator = request_generator(
        input_function(), request_size=REQUEST_SIZE, mode=RequestType.INDEX
    )
    i = 0
    async for req in generator:
        i += 1
        assert len(req.docs) == REQUEST_SIZE
        await asyncio.sleep(0.1)
    assert i == ceil(NUM_INPUT_DOCS / REQUEST_SIZE)


def test_asyncio_bad_input_generator():
    # exception not handled
    data = ['text' for _ in range(20)]
    request_generator(data, request_size=10, mode='not_index')
