import os
import pytest

from jina.flow import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize('parallel, expected_response', [(1, ['slow', 'fast']), (2, ['fast', 'slow'])])
def test_non_blocking_gateway(parallel, expected_response):
    os.environ['JINA_NON_BLOCKING_PARALLEL'] = str(parallel)
    response = []

    def fill_responses(resp):
        assert len(resp.docs) == 1
        response.append(resp.docs[0].text)

    data = [
        'slow', 'fast'
    ]
    with Flow().load_config(os.path.join(cur_dir, 'flow.yml')) as f:
        f.search(input_fn=data,
                 output_fn=fill_responses,
                 batch_size=1,
                 callback_on='body')

    del os.environ['JINA_NON_BLOCKING_PARALLEL']
    assert response == expected_response
