import pytest
import requests as req

from docarray import DocumentArray
from jina import Executor, Flow, requests


@pytest.mark.parametrize('protocol', ['http', 'grpc', 'websocket'])
@pytest.mark.parametrize('prefetch', [0, 10, 100])
@pytest.mark.parametrize('num_requests', [1, 50, 200])
def test_prefetch(protocol, prefetch, num_requests):
    with Flow(protocol=protocol, prefetch=prefetch).add() as f:
        f.post(on='/default', inputs=DocumentArray.empty(num_requests), request_size=1)


@pytest.mark.parametrize(
    'prefetch',
    [
        0,
        10,
    ],
)
@pytest.mark.parametrize('num_requests', [5, 15])
def test_prefetch_with_http_external_client(prefetch, num_requests):
    class SlowTestPrefetchExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            import time

            time.sleep(0.5)

    docs = DocumentArray.empty(num_requests)

    def rest_post(f, document):
        data = [document.to_dict()]
        response = req.post(
            f'http://localhost:{f.port}/post',
            json={'data': data},
        )

        return response.json()

    with Flow(protocol='http', prefetch=prefetch).add(
        uses=SlowTestPrefetchExecutor
    ) as f:
        for d in docs:
            _ = rest_post(f, d)
