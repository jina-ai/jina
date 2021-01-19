import os

import pytest

from ..helpers import create_flow, invoke_requests, get_results

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yml = os.path.join(cur_dir, 'flow.yml')
pod_dir = os.path.join(cur_dir, 'pods')


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_index_query(docker_compose):
    flow_id = create_flow(flow_yml, pod_dir)

    r = invoke_requests(method='post',
                        url='http://0.0.0.0:45678/api/index',
                        payload={'top_k': 10, 'data': ['text:hey, dude']})
    text_indexed = r['index']['docs'][0]['text']
    assert text_indexed == 'text:hey, dude'

    invoke_requests(method='get',
                    url=f'http://localhost:8000/flows/{flow_id}')

    invoke_requests(method='delete',
                    url=f'http://localhost:8000/flows/{flow_id}')

    flow_id = create_flow(flow_yml, pod_dir)
    assert flow_id is not None

    text_matched = get_results(
        query='text:anything will match the same')['search']['docs'][0]['matches'][0]['text']
    assert text_matched == 'text:hey, dude'

    invoke_requests(method='get',
                    url=f'http://localhost:8000/flows/{flow_id}')

    invoke_requests(method='delete',
                    url=f'http://localhost:8000/flows/{flow_id}')
    expected_text = 'text:hey, dude'
    assert expected_text == text_matched
