import os

import docker
import requests

from ..helpers import create_workspace, wait_for_workspace

cur_dir = os.path.dirname(os.path.abspath(__file__))

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version


def test_create_custom_container():
    workspace_id = create_workspace(
        filepaths=[os.path.join(cur_dir, '../../daemon/unit/models/good_ws/.jinad')]
    )
    wait_for_workspace(workspace_id)

    container_id = requests.get(
        f'http://{CLOUD_HOST}/workspaces/{workspace_id}'
    ).json()['metadata']['container_id']
    assert container_id
    container = docker.from_env().containers.get(container_id)
    assert container.name == workspace_id

    workspace_id = create_workspace(filepaths=[os.path.join(cur_dir, 'no_run.jinad')])
    wait_for_workspace(workspace_id)
    container_id = requests.get(
        f'http://{CLOUD_HOST}/workspaces/{workspace_id}'
    ).json()['metadata']['container_id']
    assert not container_id


def test_delete_custom_container():
    workspace_id = create_workspace(
        filepaths=[os.path.join(cur_dir, '../../daemon/unit/models/good_ws/.jinad')]
    )
    wait_for_workspace(workspace_id)

    # check that container was created
    response = requests.get(f'http://{CLOUD_HOST}/workspaces/{workspace_id}')
    container_id = response.json()['metadata']['container_id']
    assert container_id

    # delete container
    response = requests.delete(
        f'http://{CLOUD_HOST}/workspaces/{workspace_id}',
        params={'container': True, 'everything': False},
    )
    assert response.json()[0] == container_id

    # check that deleted container is gone
    response = requests.get(f'http://{CLOUD_HOST}/workspaces/{workspace_id}')
    assert response.status_code == 200
    container_id = response.json()['metadata']['container_id']
    assert not container_id
