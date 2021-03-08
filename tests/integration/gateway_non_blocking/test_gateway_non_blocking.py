import os

import pytest

from jina.flow import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize(
    'parallel, expected_response', [(1, ['slow', 'fast']), (2, ['fast', 'slow'])]
)
@pytest.mark.parametrize('restful', [False])
def test_non_blocking_gateway(parallel, expected_response, restful, monkeypatch):
    monkeypatch.setenv("JINA_NON_BLOCKING_PARALLEL", str(parallel))
    monkeypatch.setenv("RESTFUL", str(restful))
    response = []

    def fill_responses(resp):
        assert len(resp.docs) == 1
        response.append(resp.docs[0].text)

    data = ['slow', 'fast']

    with Flow().load_config(os.path.join(cur_dir, 'flow.yml')) as f:
        f.search(inputs=data, on_done=fill_responses, request_size=1)

    del os.environ['JINA_NON_BLOCKING_PARALLEL']
    assert response == expected_response
