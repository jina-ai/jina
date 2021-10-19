import time
import asyncio

from jina import Document
from jina.clients.request import request_generator
from jina.peapods.stream.helper import AsyncRequestsIterator

import pytest


def slow_blocking_generator():
    for i in range(2):
        yield Document(id=i)
        time.sleep(2)


@pytest.mark.asyncio
async def test_iter_requests():
    iter = request_generator(exec_endpoint='/', data=slow_blocking_generator())
    count = 0
    num_reqs = 0

    async def another_task():
        nonlocal count
        for _ in range(20):
            await asyncio.sleep(0.2)
            count += 1

    task = asyncio.create_task(another_task())
    async for _ in AsyncRequestsIterator(iter):
        """Using following code will block the event loop and count will be <5
        for _ in iter:
            ...
        """
        num_reqs += 1

    task.cancel()
    # ideally count will be 20, but to avoid flaky CI
    assert count > 15
