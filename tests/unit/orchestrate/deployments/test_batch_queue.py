import asyncio
import pytest
import time

from jina.serve.runtimes.worker.batch_queue import sleep_then_set, BatchQueue
from jina import Executor, DocumentArray, requests, Document
from jina.types.request.data import DataRequest


@pytest.mark.skip(reason="Sleep then set doesnt count normal sleep here")
@pytest.mark.asyncio
async def test_sleep_then_set():
    event = asyncio.Event()
    asyncio.create_task(sleep_then_set(0.1, event))
    assert not event.is_set()
    await asyncio.sleep(0)
    assert not event.is_set()
    await asyncio.sleep(0.2)
    assert event.is_set()

    event = asyncio.Event()
    asyncio.create_task(sleep_then_set(0.1, event))
    assert not event.is_set()
    await asyncio.sleep(0)
    assert not event.is_set()
    time.sleep(0.2)
    await asyncio.sleep(0)
    assert event.is_set()

    event = asyncio.Event()
    asyncio.create_task(sleep_then_set(0.1, event))
    for i in range(3):
        assert not event.is_set()
        time.sleep(0.1)
    assert not event.is_set()
    await asyncio.sleep(0)
    assert event.is_set()


@pytest.mark.asyncio
async def test_batch_queue():
    class MockExecutor(Executor):
        @requests
        def foo(self, docs, **kwargs):
            return DocumentArray([Document(text='Done') for _ in docs])

    executor = MockExecutor()
    args = executor.runtime_args
    args.output_array_type = None
    bq: BatchQueue = BatchQueue(
        executor=executor,
        exec_endpoint="/",
        args=args,
        preferred_batch_size=4,
        timeout=500,
    )

    data_requests = [DataRequest() for _ in range(4)]
    for req in data_requests:
        req.data.docs = DocumentArray.empty(1)
        assert req.data.docs[0].text == ''
    
    # Test preferred batch size
    events = [await bq.push(req) for req in data_requests[:-1]]
    assert len(bq._requests) == 3
    assert all(not event.is_set() for event in events)

    events.append(await bq.push(data_requests[-1]))
    assert len(bq._requests) == 4
    assert all(not event.is_set() for event in events)

    # The time here is necessary because the flush has awaits inside
    # We need to give time for the flush to finish
    await asyncio.sleep(0.2)
    assert len(bq._requests) == 0
    assert len(bq._big_doc) == 0
    assert not bq._after_flush_event.is_set()

    for event in events:
        assert event.is_set()
    
    for req in data_requests:
        assert req.data.docs[0].text == 'Done'

    # Test timeout
    for req in data_requests:
        req.data.docs[0].text = 'Not Done'
    
    single_event = await bq.push(data_requests[0])
    assert not single_event.is_set()
    assert data_requests[0].data.docs[0].text == 'Not Done'
    
    await asyncio.sleep(0)
    assert not single_event.is_set()
    assert data_requests[0].data.docs[0].text == 'Not Done'

    await asyncio.sleep(0.1)
    assert not single_event.is_set()
    assert data_requests[0].data.docs[0].text == 'Not Done'
    
    await asyncio.sleep(0.5)
    assert single_event.is_set()
    assert data_requests[0].data.docs[0].text == 'Done'
