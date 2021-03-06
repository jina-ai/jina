import os

import pytest

from ..helpers import create_workspace, create_flow_2, assert_request

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yaml = os.path.join(cur_dir, 'flow.yml')
pod_dir = os.path.join(cur_dir, 'pods')
dependencies = [
    f'{pod_dir}/index.yml',
    f'{pod_dir}/encode.yml',
    f'{pod_dir}/dummy-encoder.py',
]


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_index_query(docker_compose):
    print(f'\nCreating workspace with dependencies')
    workspace_id = create_workspace(filepaths=dependencies)

    print(f'\nCreating Flow: {flow_yaml} with workspace_id: {workspace_id}')
    index_flow_id = create_flow_2(flow_yaml=flow_yaml, workspace_id=workspace_id)

    print(f'\nIndexing: `hey, dude`')
    r = assert_request(
        method='post',
        url='http://localhost:45678/api/index',
        payload={'top_k': 10, 'data': ['text:hey, dude']},
    )
    text_indexed = r['index']['docs'][0]['text']
    assert text_indexed == 'text:hey, dude'

    print(f'\nFetching index flow id: {index_flow_id}')
    r = assert_request(method='get', url=f'http://localhost:8000/flows/{index_flow_id}')

    print(f'\nDeleting index flow id: {index_flow_id}, but keeping the workspace alive')
    r = assert_request(
        method='delete',
        url=f'http://localhost:8000/flows/{index_flow_id}',
        payload={'workspace': False},
    )

    print(f'\nCreating query Flow {flow_yaml} with workspace_id: {workspace_id}')
    query_flow_id = create_flow_2(flow_yaml=flow_yaml, workspace_id=workspace_id)
    assert query_flow_id is not None

    print(f'\nQuerying any text')
    r = assert_request(
        method='post',
        url='http://0.0.0.0:45678/api/search',
        payload={'top_k': 10, 'data': ['text:anything will match the same']},
    )
    print(f'returned: {r}')
    text_matched = r['search']['docs'][0]['matches'][0]['text']
    assert text_matched == 'text:hey, dude'

    print(f'\nFetching query flow id: {query_flow_id}')
    assert_request(method='get', url=f'http://localhost:8000/flows/{query_flow_id}')

    print(f'\nDeleting query flow id: {index_flow_id}, along with the workspace')
    assert_request(
        method='delete',
        url=f'http://localhost:8000/flows/{query_flow_id}',
        payload={'workspace': True},
    )
