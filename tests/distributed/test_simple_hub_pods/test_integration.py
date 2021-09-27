import os

import pytest

from jina import __default_host__, __docker_host__
from ..helpers import create_workspace, wait_for_workspace, create_flow, assert_request

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yaml = os.path.join(cur_dir, 'flow.yml')

JINAD_HOST = __default_host__
GATEWAY_HOST = __default_host__
JINAD_PORT = 8000
GATEWAY_PORT = 45630


@pytest.mark.skip('jinad with docker-compose not supported for now')
@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_simple_hub_pods(docker_compose):
    workspace_id = create_workspace(filepaths=[flow_yaml])
    assert wait_for_workspace(workspace_id)
    flow_id = create_flow(workspace_id=workspace_id, filename='flow.yml')
    expected_text = 'text:hey, dude'
    response = assert_request(
        method='post',
        url=f'http://{GATEWAY_HOST}:{GATEWAY_PORT}/search',
        payload={'top_k': 10, 'data': [expected_text]},
    )
    print(f'Response is: {response}')

    assert expected_text + ' hurray' * 2 == response['data']['docs'][0]['text']

    assert_request(
        method='get', url=f'http://{JINAD_HOST}:{JINAD_PORT}/flows/{flow_id}'
    )
    assert_request(
        method='delete',
        url=f'http://{JINAD_HOST}:{JINAD_PORT}/flows/{flow_id}',
    )
