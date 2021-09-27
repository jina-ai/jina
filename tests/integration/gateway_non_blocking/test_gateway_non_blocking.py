import pytest

from jina import Flow, Executor, requests, DocumentArray, Document

import time


class FastSlowExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @requests(on=['/search'])
    def encode(self, docs: DocumentArray, *args, **kwargs):
        assert len(docs) == 1
        if docs[0].text == 'slow':
            time.sleep(2)


@pytest.mark.parametrize(
    'parallel, expected_response', [(1, ['slow', 'fast']), (2, ['fast', 'slow'])]
)
def test_non_blocking_gateway(parallel, expected_response):
    response = []

    def fill_responses(resp):
        assert len(resp.data.docs) == 1
        response.append(resp.data.docs[0].text)

    data = DocumentArray([Document(text='slow'), Document(text='fast')])

    f = Flow().add(uses=FastSlowExecutor, parallel=parallel)
    with f:
        f.post(on='/search', inputs=data, request_size=1, on_done=fill_responses)

    assert response == expected_response
