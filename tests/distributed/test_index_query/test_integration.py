import os

import pytest

from ..helpers import create_flow, assert_request, get_results

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yml = os.path.join(cur_dir, 'flow.yml')
pod_dir = os.path.join(cur_dir, 'pods')


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_index_query(docker_compose):
    index_flow_id = create_flow(flow_yml, pod_dir)

    r = assert_request(method='post',
                       url='http://0.0.0.0:45678/api/index',
                       payload={'top_k': 10, 'data': ['text:hey, dude']})
    text_indexed = r['index']['docs'][0]['text']
    assert text_indexed == 'text:hey, dude'

    r = assert_request(method='get',
                       url=f'http://localhost:8000/flows/{index_flow_id}')

    # reuse the index workspace
    query_flow_id = create_flow(flow_yml, pod_dir, workspace_id=r['workspace_id'])
    assert query_flow_id is not None

    r = get_results(
        query='text:anything will match the same')['search']['docs'][0]
    print(f'returned: {r}')
    text_matched = r['matches'][0]['text']
    assert text_matched == 'text:hey, dude'

    assert_request(method='get',
                   url=f'http://localhost:8000/flows/{query_flow_id}')

    assert_request(method='delete',
                   url=f'http://localhost:8000/flows/{query_flow_id}')

    assert_request(method='delete',
                   url=f'http://localhost:8000/flows/{index_flow_id}')
