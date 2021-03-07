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
    f'{pod_dir}/slice.yml',
    f'{pod_dir}/dummy-encoder.py',
]


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_flow(docker_compose):
    print(f'\nCreating workspace with dependencies')
    workspace_id = create_workspace(filepaths=dependencies)

    print(f'\nCreating Flow: {flow_yaml} with workspace_id: {workspace_id}')
    index_flow_id = create_flow_2(flow_yaml=flow_yaml, workspace_id=workspace_id)

    for x in range(100):
        text = 'text:hey, dude ' + str(x)
        print(f'Indexing with text: {text}')
        r = assert_request(
            method='post',
            url='http://0.0.0.0:45678/api/index',
            payload={'top_k': 10, 'data': [text]},
        )
        text_indexed = r['index']['docs'][0]['text']
        print(f'Got response text_indexed: {text_indexed}')
        # assert text_indexed == text

    assert_request(method='get', url=f'http://localhost:8000/flows/{index_flow_id}')

    assert_request(
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
        payload={'top_k': 100, 'data': ['text:anything will match the same']},
    )
    print(f'returned: {r}')
    texts_matched = r['search']['docs'][0]['matches']
    assert len(texts_matched) == 100

    assert_request(method='get', url=f'http://localhost:8000/flows/{query_flow_id}')

    assert_request(
        method='delete',
        url=f'http://localhost:8000/flows/{query_flow_id}',
        payload={'workspace': True},
    )
