import time

import pytest

from jina import Document, DocumentArray, Executor, Flow, requests


@pytest.mark.parametrize(
    'shards, expected_response', [(1, ['slow', 'fast']), (2, ['fast', 'slow'])]
)
def test_non_blocking_gateway(shards, expected_response):
    class FastSlowExecutor(Executor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        @requests(on=['/custom'])
        def encode(self, docs: DocumentArray, *args, **kwargs):
            assert len(docs) == 1
            if docs[0].text == 'slow':
                time.sleep(2)

    response = []

    def fill_responses(resp):
        assert len(resp.data.docs) == 1
        response.append(resp.data.docs[0].text)

    data = DocumentArray([Document(text='slow'), Document(text='fast')])

    f = Flow().add(uses=FastSlowExecutor, shards=shards, polling='ANY')
    with f:
        f.post(on='/custom', inputs=data, request_size=1)
        # first request is not to be trusted because of discovery endpoint
        f.post(on='/custom', inputs=data, request_size=1, on_done=fill_responses)
    assert response == expected_response
