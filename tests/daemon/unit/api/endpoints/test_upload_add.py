import os
from pathlib import Path

import pytest

from daemon.stores.helper import get_workspace_path

cur_dir = Path(__file__).parent

deps = ['mwu_encoder.py', 'mwu_encoder.yml', 'logging.log']

lines = """
{"host":"ubuntu","process":"32539","type":"INFO","name":"encode1","uptime":"20210124215151","context":"encode1","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"starting jina.peapods.runtimes.zmq.zed.ZEDRuntime..."}
{"host":"ubuntu","process":"32539","type":"INFO","name":"encode1","uptime":"20210124215151","context":"encode1/ZEDRuntime","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"input \u001B[33mtcp://0.0.0.0:45319\u001B[0m (PULL_BIND) output \u001B[33mtcp://0.0.0.0:59229\u001B[0m (PUSH_CONNECT) control over \u001B[33mtcp://0.0.0.0:49571\u001B[0m (PAIR_BIND)"}
{"host":"ubuntu","process":"31612","type":"SUCCESS","name":"encode1","uptime":"20210124215151","context":"encode1","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"ready and listening"}
{"host":"ubuntu","process":"32546","type":"INFO","name":"encode2","uptime":"20210124215151","context":"encode2","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"starting jina.peapods.runtimes.zmq.zed.ZEDRuntime..."}
"""

with open('tests/daemon/unit/api/endpoints/logging.log', 'w') as f:
    f.writelines(lines)


@pytest.mark.parametrize('api', ['/peas', 'pods'])
@pytest.mark.parametrize('workspace', [True, False])
def test_upload_then_add_success(api, workspace, fastapi_client):
    # Upload files to workspace
    response = fastapi_client.post(
        '/workspaces', files=[('files', open(str(cur_dir / d), 'rb')) for d in deps]
    )
    assert response.status_code == 201
    workspace_id = response.json()
    assert os.path.exists(get_workspace_path(workspace_id))
    for d in deps:
        assert os.path.exists(get_workspace_path(workspace_id, d))

    # Create a Pea/Pod
    response = fastapi_client.post(
        api, json={'uses': 'mwu_encoder.yml', 'workspace_id': workspace_id}
    )
    assert response.status_code == 201
    _id = response.json()

    # Fetch all Peas/Pods
    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['size'] == 1

    # Fetch the Pea/Pod ID
    response = fastapi_client.get(f'{api}/{_id}')
    assert response.status_code == 200
    assert 'time_created' in response.json()
    workdir = response.json()['workdir']
    assert os.path.exists(workdir)
    for d in deps:
        assert os.path.exists(os.path.join(workdir, d))

    # Delete the Pea/Pod along with the workspace parameter.
    # If workspace=True, this should delete all files in workspace except logging.log
    # If workspace=False, this shouldn't delete anything from the workspace
    response = fastapi_client.delete(f'{api}/{_id}?workspace={str(workspace)}')
    assert response.status_code == 200
    if workspace:
        for d in deps:
            if d == 'logging.log':
                assert os.path.exists(os.path.join(workdir, d))
            else:
                assert not os.path.exists(os.path.join(workdir, d))
    else:
        for d in deps:
            assert os.path.exists(os.path.join(workdir, d))

    # Fetch all Peas/Pods & check for
    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['size'] == 0


@pytest.mark.parametrize('workspace', [True, False])
def test_upload_then_add_flow_success(workspace, fastapi_client):
    # Upload files to workspace
    response = fastapi_client.post(
        '/workspaces', files=[('files', open(str(cur_dir / d), 'rb')) for d in deps]
    )
    assert response.status_code == 201
    workspace_id = response.json()

    # Create a Flow
    response = fastapi_client.post(
        '/flows',
        files={
            'flow': ('good_flow.yml', open(str(cur_dir / 'good_flow_dep.yml'), 'rb')),
            'workspace_id': (None, workspace_id),
        },
    )
    assert response.status_code == 201
    _id = response.json()

    # Fetch all Flows
    response = fastapi_client.get('/flows')
    assert response.status_code == 200
    assert response.json()['size'] == 1

    # Fetch the Flow ID
    response = fastapi_client.get(f'/flows/{_id}')
    assert response.status_code == 200
    assert 'time_created' in response.json()
    workdir = response.json()['workdir']
    assert os.path.exists(workdir)
    for d in deps:
        assert os.path.exists(os.path.join(workdir, d))

    # Delete the Flow along with the workspace parameter.
    # If workspace=True, this should delete all files in workspace except logging.log
    # If workspace=False, this shouldn't delete anything from the workspace
    response = fastapi_client.delete(f'/flows/{_id}?workspace={str(workspace)}')
    assert response.status_code == 200
    if workspace:
        for d in deps:
            if d == 'logging.log':
                assert os.path.exists(os.path.join(workdir, d))
            else:
                assert not os.path.exists(os.path.join(workdir, d))
    else:
        for d in deps:
            assert os.path.exists(os.path.join(workdir, d))

    response = fastapi_client.get('/flows')
    assert response.status_code == 200
    assert response.json()['size'] == 0


def test_post_and_delete_workspace(fastapi_client):
    response = fastapi_client.post(
        '/workspaces', files=[('files', open(str(cur_dir / d), 'rb')) for d in deps]
    )
    assert response.status_code == 201
    workspace_id = response.json()
    assert os.path.exists(get_workspace_path(workspace_id))
    for d in deps:
        assert os.path.exists(get_workspace_path(workspace_id, d))

    response = fastapi_client.delete(f'/workspaces/{workspace_id}')
    assert response.status_code == 200
    assert not os.path.exists(get_workspace_path(workspace_id))
