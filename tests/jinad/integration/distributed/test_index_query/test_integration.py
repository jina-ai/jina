import os

import pytest

from ..helpers import create_flow, invoke_requests, get_results

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yml = os.path.join(cur_dir, 'flow.yml')
pod_dir = os.path.join(cur_dir, 'pods')


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_index_query(docker_compose):
    flow_id = create_flow(flow_yml, pod_dir)['flow_id']
    print(f'Flow created with id {flow_id}')

    r = invoke_requests(method='post',
                        url='http://0.0.0.0:45678/api/index',
                        payload={'top_k': 10, 'data': ['text:hey, dude']})
    assert r is not None
    text_indexed = r['index']['docs'][0]['text']
    assert text_indexed == 'text:hey, dude'

    r = invoke_requests(method='get',
                        url=f'http://localhost:8000/flow/{flow_id}')
    assert r is not None
    assert r['status_code'] == 200

    r = invoke_requests(method='delete',
                        url=f'http://localhost:8000/flow?flow_id={flow_id}')
    assert r is not None
    assert r['status_code'] == 200

    flow_id = create_flow(flow_yml, pod_dir)['flow_id']
    assert flow_id is not None

    text_matched = get_results(
        query='text:anything will match the same')['search']['docs'][0]['matches'][0]['text']
    assert text_matched == 'text:hey, dude'

    r = invoke_requests(method='get',
                        url=f'http://localhost:8000/flow/{flow_id}')
    assert r is not None
    assert r['status_code'] == 200

    r = invoke_requests(method='delete',
                        url=f'http://localhost:8000/flow?flow_id={flow_id}')
    assert r is not None
    assert r['status_code'] == 200
    expected_text = 'text:hey, dude'
    assert expected_text == text_matched
