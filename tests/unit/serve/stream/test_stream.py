import asyncio
import random

import pytest

from jina import Document, DocumentArray
from jina.helper import Namespace, random_identity
from jina.serve.stream import RequestStreamer
from jina.types.request.data import DataRequest


class RequestStreamerWrapper:
    def __init__(self, num_requests, prefetch, iterate_sync_in_thread):
        self.num_requests = num_requests
        self.requests_handled = []
        self.results_handled = []
        self.request_ids = [random_identity() for _ in range(num_requests)]
        self.response_ids = []

        args = Namespace()
        args.prefetch = prefetch
        self.streamer = RequestStreamer(
            request_handler=self.request_handler_fn,
            result_handler=self.result_handle_fn,
            end_of_iter_handler=self.end_of_iter_fn,
            prefetch=getattr(args, 'prefetch', 0),
            iterate_sync_in_thread=iterate_sync_in_thread
        )

    def request_handler_fn(self, request):
        self.requests_handled.append(request)

        async def task():
            rand_sleep = random.uniform(0.1, 0.6)
            await asyncio.sleep(rand_sleep)
            docs = request.docs
            docs[0].tags['request_handled'] = True
            request.data.docs = docs
            return request

        future = asyncio.ensure_future(task())
        return future, None

    def result_handle_fn(self, result):
        self.results_handled.append(result)
        assert isinstance(result, DataRequest)
        docs = result.docs
        docs[0].tags['result_handled'] = True
        result.data.docs = docs
        return result

    def end_of_iter_fn(self):
        # with a sync generator, iteration
        assert len(self.requests_handled) == self.num_requests
        assert len(self.results_handled) <= self.num_requests

    def _yield_data_request(self, i):
        req = DataRequest()
        req.header.request_id = self.request_ids[i]
        da = DocumentArray()
        da.append(Document())
        req.data.docs = da
        return req

    def _get_sync_requests_iterator(self):
        for i in range(self.num_requests):
            yield self._yield_data_request(i)

    async def _get_async_requests_iterator(self):
        for i in range(self.num_requests):
            yield self._yield_data_request(i)
            await asyncio.sleep(0.1)


@pytest.mark.asyncio
@pytest.mark.parametrize('prefetch', [0, 5])
@pytest.mark.parametrize('num_requests', [1, 5, 13])
@pytest.mark.parametrize('async_iterator', [False, True])
@pytest.mark.parametrize('results_in_order', [False, True])
@pytest.mark.parametrize('iterate_sync_in_thread', [False, True])
async def test_request_streamer(
    prefetch, num_requests, async_iterator, results_in_order, iterate_sync_in_thread
):

    test_streamer = RequestStreamerWrapper(num_requests, prefetch, iterate_sync_in_thread)
    streamer = test_streamer.streamer

    it = (
        test_streamer._get_async_requests_iterator()
        if async_iterator
        else test_streamer._get_sync_requests_iterator()
    )
    response = streamer.stream(request_iterator=it, results_in_order=results_in_order)

    num_responses = 0

    async for r in response:
        test_streamer.response_ids.append(r.header.request_id)
        num_responses += 1
        assert r.docs[0].tags['request_handled']
        assert r.docs[0].tags['result_handled']

    assert num_responses == num_requests
    assert len(test_streamer.request_ids) == len(test_streamer.response_ids)

    if results_in_order:
        for req_id, resp_id in zip(
            test_streamer.request_ids, test_streamer.response_ids
        ):
            assert req_id == resp_id


@pytest.mark.asyncio
@pytest.mark.parametrize('num_requests', [1, 5, 13])
@pytest.mark.parametrize('iterate_sync_in_thread', [False, True])
async def test_request_streamer_process_single_data(monkeypatch, num_requests, iterate_sync_in_thread):
    test_streamer = RequestStreamerWrapper(num_requests, 0, iterate_sync_in_thread)
    streamer = test_streamer.streamer

    def end_of_iter_fn():
        # bypass some assertions in RequestStreamerWrapper.end_of_iter_fn
        pass

    monkeypatch.setattr(streamer, '_end_of_iter_handler', end_of_iter_fn)

    it = test_streamer._get_sync_requests_iterator()

    num_responses = 0

    for req in it:
        r = await streamer.process_single_data(request=req)
        test_streamer.response_ids.append(r.header.request_id)
        num_responses += 1
        assert r.docs[0].tags['request_handled']
        assert r.docs[0].tags['result_handled']

    assert num_responses == num_requests
    assert len(test_streamer.request_ids) == len(test_streamer.response_ids)
