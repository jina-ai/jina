import asyncio

import pytest

from jina.clients.request.async_batch import batch_iterator


async def input_fn():
    for j in range(10):
        yield j
        await asyncio.sleep(.1)


@pytest.mark.asyncio
async def test_batch_iterator():
    async for batch in batch_iterator(input_fn, 3):
        print(batch)
