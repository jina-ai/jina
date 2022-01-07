import asyncio
import pytest

from jina import Document
from jina.helper import Namespace, random_identity
from jina.peapods.stream import RequestStreamer
from jina.proto import jina_pb2
from jina.types.request.data import DataRequest


@pytest.mark.asyncio
@pytest.mark.parametrize('prefetch', [0, 5])
@pytest.mark.parametrize('num_requests', [1, 5, 13])
@pytest.mark.parametrize('async_iterator', [False, True])
async def test_request_streamer(prefetch, num_requests, async_iterator):
    requests_handled = []
    results_handled = []

    def request_handler_fn(request):
        requests_handled.append(request)

        async def task():
            await asyncio.sleep(0.5)
            request.docs[0].tags['request_handled'] = True
            return request

        future = asyncio.ensure_future(task())
        return future

    def result_handle_fn(result):
        results_handled.append(result)
        assert isinstance(result, DataRequest)
        result.docs[0].tags['result_handled'] = True
        return result

    def end_of_iter_fn():
        # with a sync generator, iteration
        assert len(requests_handled) == num_requests
        assert len(results_handled) < num_requests

    def _get_sync_requests_iterator(num_requests):
        for i in range(num_requests):
            req = DataRequest()
            req.header.request_id = random_identity()
            req.docs.append(Document())
            yield req

    async def _get_async_requests_iterator(num_requests):
        for i in range(num_requests):
            req = DataRequest()
            req.header.request_id = random_identity()
            req.docs.append(Document())
            yield req
            await asyncio.sleep(0.1)

    args = Namespace()
    args.prefetch = prefetch
    streamer = RequestStreamer(
        args=args,
        request_handler=request_handler_fn,
        result_handler=result_handle_fn,
        end_of_iter_handler=end_of_iter_fn,
    )

    it = (
        _get_async_requests_iterator(num_requests)
        if async_iterator
        else _get_sync_requests_iterator(num_requests)
    )
    response = streamer.stream(it)

    num_responses = 0

    async for r in response:
        num_responses += 1
        assert r.docs[0].tags['request_handled']
        assert r.docs[0].tags['result_handled']

    assert num_responses == num_requests
