import asyncio
import random

import pytest

from jina import Document, DocumentArray
from jina.helper import Namespace, random_identity
from jina.serve.stream import RequestStreamer
from jina.types.request.data import DataRequest


@pytest.mark.asyncio
@pytest.mark.parametrize('prefetch', [0, 5])
@pytest.mark.parametrize('num_requests', [1, 5, 13])
@pytest.mark.parametrize('async_iterator', [False, True])
@pytest.mark.parametrize('results_in_order', [False, True])
async def test_request_streamer(
    prefetch, num_requests, async_iterator, results_in_order
):
    requests_handled = []
    results_handled = []

    request_ids = [random_identity() for _ in range(num_requests)]
    response_ids = []

    def request_handler_fn(request):
        requests_handled.append(request)

        async def task():
            rand_sleep = random.uniform(0.1, 0.6)
            await asyncio.sleep(rand_sleep)
            docs = request.docs
            docs[0].tags['request_handled'] = True
            request.data.docs = docs
            return request

        future = asyncio.ensure_future(task())
        return future, None

    def result_handle_fn(result):
        results_handled.append(result)
        assert isinstance(result, DataRequest)
        docs = result.docs
        docs[0].tags['result_handled'] = True
        result.data.docs = docs
        return result

    def end_of_iter_fn():
        # with a sync generator, iteration
        assert len(requests_handled) == num_requests
        assert len(results_handled) <= num_requests

    def _yield_data_request(i):
        req = DataRequest()
        req.header.request_id = request_ids[i]
        da = DocumentArray()
        da.append(Document())
        req.data.docs = da
        return req

    def _get_sync_requests_iterator(num_requests):
        for i in range(num_requests):
            yield _yield_data_request(i)

    async def _get_async_requests_iterator(num_requests):
        for i in range(num_requests):
            yield _yield_data_request(i)
            await asyncio.sleep(0.1)

    args = Namespace()
    args.prefetch = prefetch
    streamer = RequestStreamer(
        request_handler=request_handler_fn,
        result_handler=result_handle_fn,
        end_of_iter_handler=end_of_iter_fn,
        prefetch=getattr(args, 'prefetch', 0),
    )

    it = (
        _get_async_requests_iterator(num_requests)
        if async_iterator
        else _get_sync_requests_iterator(num_requests)
    )
    response = streamer.stream(request_iterator=it, results_in_order=results_in_order)

    num_responses = 0

    async for r in response:
        response_ids.append(r.header.request_id)
        num_responses += 1
        assert r.docs[0].tags['request_handled']
        assert r.docs[0].tags['result_handled']

    assert num_responses == num_requests
    assert len(request_ids) == len(response_ids)

    if results_in_order:
        for req_id, resp_id in zip(request_ids, response_ids):
            assert req_id == resp_id
