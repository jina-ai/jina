import os
from pathlib import Path

from daemon.helper import get_workspace_path
from daemon.models.workspaces import WorkspaceItem
from jina.enums import RemoteWorkspaceState

cur_dir = Path(__file__).parent

deps = ['mwu_encoder.py', 'mwu_encoder.yml']


def test_main(fastapi_client):
    response = fastapi_client.get('/')
    assert response.status_code == 200
    assert response.json() == {}


def test_status(fastapi_client):
    response = fastapi_client.get('/status')
    assert response.status_code == 200
    for k in ('jina', 'envs', 'workspaces', 'peas', 'pods', 'flows', 'used_memory'):
        assert k in response.json()


def test_upload(fastapi_client):
    response = fastapi_client.post(
        '/workspaces', files=[('files', open(str(cur_dir / d), 'rb')) for d in deps]
    )
    assert response.status_code == 201
    response_json = response.json()
    workspace_id = next(iter(response_json))
    item = WorkspaceItem(**response_json[workspace_id])
    assert item.state == RemoteWorkspaceState.PENDING
    assert item.metadata is None
    assert item.arguments is None

    for d in deps:
        os.path.exists(get_workspace_path(workspace_id, d))
