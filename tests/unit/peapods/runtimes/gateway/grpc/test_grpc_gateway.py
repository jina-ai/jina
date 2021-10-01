import asyncio
from threading import Thread

import pytest
import time
from jina import Flow, Document, Client


@pytest.mark.slow
@pytest.mark.timeout(5)
@pytest.mark.parametrize('prefetch', [1])
def test_disable_prefetching(prefetch):
    sleep_time = 1.0

    def response_checker(response):
        start_time = float(response.data.docs[0].text)
        response_time = time.time() - start_time
        print(f'got response at {time.time()} this took {response_time}', flush=True)
        # the response should not be delayed by the slow generator sleeping
        assert response_time < sleep_time

    def slow_gen():
        for j in range(1):
            print(f'yield document at {time.time()}', flush=True)
            yield Document(content=str(time.time()))
            time.sleep(sleep_time)
            print(f'sleep over at {time.time()}', flush=True)

    with Flow(prefetch=prefetch) as f:
        f.post('/', slow_gen(), request_size=1, on_done=response_checker)


@pytest.mark.slow
@pytest.mark.timeout(5)
@pytest.mark.asyncio
@pytest.mark.parametrize('prefetch', [1])
async def test_disable_prefetching_async(prefetch):
    sleep_time = 1.0

    def response_checker(response):
        start_time = float(response.data.docs[0].text)
        response_time = time.time() - start_time
        print(f'got response at {time.time()} this took {response_time}', flush=True)
        # the response should not be delayed by the slow generator sleeping
        assert response_time < sleep_time

    async def slow_gen():
        for j in range(1):
            print(f'yield document at {time.time()}', flush=True)
            yield Document(content=str(time.time()))
            await asyncio.sleep(sleep_time)
            print(f'sleep over at {time.time()}', flush=True)

    with Flow(prefetch=prefetch) as f:
        c = Client(host='localhost', port=f.port_expose, asyncio=True)
        r = c.post('/', slow_gen(), request_size=1, on_done=response_checker)
        response = await r.__anext__()
        print(response)
