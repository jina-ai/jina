import os

import pytest

from ..helpers import create_flow, assert_request

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yml = os.path.join(cur_dir, 'flow.yml')
pod_dir = os.path.join(cur_dir, 'pods')


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_flow(docker_compose):
    flow_id = create_flow(flow_yml, pod_dir)
    print(f'Flow created with id {flow_id}')

    r = assert_request(
        method='post',
        url='http://0.0.0.0:45678/api/search',
        payload={'top_k': 10, 'data': ['text:cats rulessss']},
    )
    assert r is not None
    text_indexed = r['search']['docs'][0]['text']
    print(f'Got response text_indexed: {text_indexed}')
    assert text_indexed == 'text:cats rulessss'

    assert_request(method='get', url=f'http://localhost:8000/flows/{flow_id}')

    assert_request(method='delete', url=f'http://localhost:8000/flows/{flow_id}')
