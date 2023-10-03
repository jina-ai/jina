import asyncio

import pytest
import time

from jina import Document, DocumentArray
from jina.serve.runtimes.worker.batch_queue import BatchQueue
from jina.types.request.data import DataRequest


@pytest.mark.asyncio
async def test_batch_queue_timeout():
    async def foo(docs, **kwargs):
        await asyncio.sleep(0.1)
        return DocumentArray([Document(text='Done') for _ in docs])

    bq: BatchQueue = BatchQueue(
        foo,
        request_docarray_cls=DocumentArray,
        response_docarray_cls=DocumentArray,
        preferred_batch_size=4,
        timeout=2000,
    )

    three_data_requests = [DataRequest() for _ in range(3)]
    for req in three_data_requests:
        req.data.docs = DocumentArray.empty(1)
        assert req.data.docs[0].text == ''

    async def process_request(req):
        q = await bq.push(req)
        _ = await q.get()
        q.task_done()
        return req

    init_time = time.time()
    tasks = [asyncio.create_task(process_request(req)) for req in three_data_requests]
    responses = await asyncio.gather(*tasks)
    time_spent = (time.time() - init_time) * 1000
    assert time_spent >= 2000
    # Test that since no more docs arrived, the function was triggerred after timeout
    for resp in responses:
        assert resp.data.docs[0].text == 'Done'

    four_data_requests = [DataRequest() for _ in range(4)]
    for req in four_data_requests:
        req.data.docs = DocumentArray.empty(1)
        assert req.data.docs[0].text == ''
    init_time = time.time()
    tasks = [asyncio.create_task(process_request(req)) for req in four_data_requests]
    responses = await asyncio.gather(*tasks)
    time_spent = (time.time() - init_time) * 1000
    assert time_spent < 2000
    # Test that since no more docs arrived, the function was triggerred after timeout
    for resp in responses:
        assert resp.data.docs[0].text == 'Done'

    await bq.close()


@pytest.mark.asyncio
async def test_batch_queue_req_length_larger_than_preferred():
    async def foo(docs, **kwargs):
        await asyncio.sleep(0.1)
        return DocumentArray([Document(text='Done') for _ in docs])

    bq: BatchQueue = BatchQueue(
        foo,
        request_docarray_cls=DocumentArray,
        response_docarray_cls=DocumentArray,
        preferred_batch_size=4,
        timeout=2000,
    )

    data_requests = [DataRequest() for _ in range(3)]
    for req in data_requests:
        req.data.docs = DocumentArray.empty(10) # 30 docs in total
        assert req.data.docs[0].text == ''

    async def process_request(req):
        q = await bq.push(req)
        _ = await q.get()
        q.task_done()
        return req

    init_time = time.time()
    tasks = [asyncio.create_task(process_request(req)) for req in data_requests]
    responses = await asyncio.gather(*tasks)
    time_spent = (time.time() - init_time) * 1000
    assert time_spent < 2000
    # Test that since no more docs arrived, the function was triggerred after timeout
    for resp in responses:
        assert resp.data.docs[0].text == 'Done'

    await bq.close()


@pytest.mark.asyncio
async def test_exception():
    BAD_REQUEST_IDX = [2, 6]

    async def foo(docs, **kwargs):
        assert len(docs) == 1
        if docs[0].text == 'Bad':
            raise Exception
        for doc in docs:
            doc.text = 'Processed'

    bq: BatchQueue = BatchQueue(
        foo,
        request_docarray_cls=DocumentArray,
        response_docarray_cls=DocumentArray,
        preferred_batch_size=1,
        timeout=500,
    )

    data_requests = [DataRequest() for _ in range(10)]
    for i, req in enumerate(data_requests):
        req.data.docs = DocumentArray(Document(text='' if i not in BAD_REQUEST_IDX else 'Bad'))

    async def process_request(req):
        q = await bq.push(req)
        item = await q.get()
        q.task_done()
        return item

    tasks = [asyncio.create_task(process_request(req)) for req in data_requests]
    items = await asyncio.gather(*tasks)
    for i, item in enumerate(items):
        if i not in BAD_REQUEST_IDX:
            assert item is None
        else:
            assert isinstance(item, Exception)
    for i, req in enumerate(data_requests):
        if i not in BAD_REQUEST_IDX:
            assert req.data.docs[0].text == 'Processed'
        else:
            assert req.data.docs[0].text == 'Bad'


@pytest.mark.asyncio
async def test_repr_and_str():
    async def foo(docs, **kwargs):
        return DocumentArray([Document(text='Done') for _ in docs])

    bq: BatchQueue = BatchQueue(
        foo,
        request_docarray_cls=DocumentArray,
        response_docarray_cls=DocumentArray,
        preferred_batch_size=4,
        timeout=500,
    )

    assert repr(bq) == str(bq)
