import asyncio
import time

import pytest

from docarray import Document
from jina.clients.request import request_generator
from jina.serve.stream.helper import AsyncRequestsIterator, _RequestsCounter


def slow_blocking_generator():
    for i in range(2):
        yield Document(id=str(i))
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


@pytest.mark.asyncio
async def test_iter_requests_with_prefetch():

    max_amount_requests = _RequestsCounter()
    counter = _RequestsCounter()

    async def consume_requests():
        while True:
            await asyncio.sleep(0.01)
            if counter.count > 0:
                counter.count -= 1

    async def req_iterator(max_amount_requests):
        for i in range(1000):
            await asyncio.sleep(0.001)
            counter.count += 1
            if counter.count > max_amount_requests.count:
                max_amount_requests.count = counter.count
            yield i

    consume_task = asyncio.create_task(consume_requests())
    async for _ in AsyncRequestsIterator(
        req_iterator(max_amount_requests), counter, 10
    ):
        pass

    consume_task.cancel()
    assert max_amount_requests.count == 10
