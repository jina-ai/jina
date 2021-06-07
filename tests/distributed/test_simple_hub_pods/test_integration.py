import os

import pytest

from ..helpers import (
    create_workspace,
    wait_for_workspace,
    create_flow,
    assert_request
)

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yaml = os.path.join(cur_dir, 'flow.yml')


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_simple_hub_pods(docker_compose):
    workspace_id = create_workspace(filepaths=[flow_yaml])
    assert wait_for_workspace(workspace_id)
    index_flow_id = create_flow(workspace_id=workspace_id,
                                filename='flow.yml')
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
