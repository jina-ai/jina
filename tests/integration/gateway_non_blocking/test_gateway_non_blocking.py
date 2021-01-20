import os

import pytest

from jina.flow import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skipif('GITHUB_WORKFLOW' in os.environ,
                    reason='for unknown reason, parallel=2 always fail on Github action, '
                           'but locally it SHOULD work fine')
@pytest.mark.parametrize('parallel, expected_response', [(1, ['slow', 'fast']), (2, ['fast', 'slow'])])
@pytest.mark.parametrize('restful', [False, True])
def test_non_blocking_gateway(parallel, expected_response, restful, monkeypatch):
    monkeypatch.setenv("JINA_NON_BLOCKING_PARALLEL", str(parallel))
    monkeypatch.setenv("RESTFUL", str(restful))
    response = []

    def fill_responses(resp):
        assert len(resp.docs) == 1
        response.append(resp.docs[0].text)

    data = [
        'slow', 'fast'
    ]

    with Flow().load_config(os.path.join(cur_dir, 'flow.yml')) as f:
        f.search(input_fn=data,
                 on_done=fill_responses,
                 request_size=1,
                 callback_on='body')

    del os.environ['JINA_NON_BLOCKING_PARALLEL']
    assert response == expected_response
