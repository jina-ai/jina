import asyncio
from math import ceil

import pytest

from jina import Document
from jina.clients.request.asyncio import request_generator

NUM_INPUT_DOCS = 30
REQUEST_SIZE = 10


@pytest.mark.asyncio
async def test_asyncio_req_generator():
    async def input_function():
        data = [Document() for _ in range(NUM_INPUT_DOCS)]
        for doc in data:
            yield doc

    generator = request_generator('/', input_function(), request_size=REQUEST_SIZE)
    i = 0
    async for req in generator:
        i += 1
        assert len(req.docs) == REQUEST_SIZE
        await asyncio.sleep(0.1)
    assert i == ceil(NUM_INPUT_DOCS / REQUEST_SIZE)


@pytest.mark.asyncio
async def test_asyncio_req_generator_empty_inputs():
    generator = request_generator('/', None)
    i = 0
    async for req in generator:
        i += 1
        assert len(req.docs) == 0
        await asyncio.sleep(0.1)
    assert i == 1


def test_asyncio_bad_input_generator():
    # exception not handled
    data = ['text' for _ in range(20)]
    request_generator('/', data, request_size=10)
