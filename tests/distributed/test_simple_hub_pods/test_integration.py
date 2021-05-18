import os

import pytest

from ..helpers import create_flow, create_flow_2, assert_request

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yaml = os.path.join(cur_dir, 'flow.yml')
pod_dir = os.path.join(cur_dir, 'pods')


@pytest.mark.skip(
    reason='using daemon for container runtime is untest and unimplemented'
)
@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_simple_hub_pods(docker_compose):
    print(f'\nCreating Flow: {flow_yaml} with empty workspace_id')
    index_flow_id = create_flow_2(flow_yaml=flow_yaml)

    expected_text = 'text:hey, dude'
    response = assert_request(
        method='post',
        url='http://0.0.0.0:45678/search',
        payload={'top_k': 10, 'data': [expected_text]},
    )
    print(f'Response is: {response}')

    print(f'\nQuerying any text')
    r = assert_request(
        method='post',
        url='http://0.0.0.0:45678/search',
        payload={'top_k': 10, 'data': ['text:anything will match the same']},
    )
    print(f'returned: {r}')
    text_matched = r['data']['docs'][0]['matches'][0]['text']
    assert expected_text == text_matched

    assert_request(method='get', url=f'http://0.0.0.0:8000/flow/{index_flow_id}')

    assert_request(
        method='delete', url=f'http://0.0.0.0:8000/flow?flow_id={index_flow_id}'
    )
