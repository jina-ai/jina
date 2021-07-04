import os

import docker
import requests

from ..helpers import create_workspace, wait_for_workspace

cur_dir = os.path.dirname(os.path.abspath(__file__))

"""
Run below commands for local tests
docker build --build-arg PIP_TAG=daemon -f Dockerfiles/debianx.Dockerfile -t jinaai/jina:test-daemon .
docker run --add-host host.docker.internal:host-gateway \
    --name jinad -v /var/run/docker.sock:/var/run/docker.sock -v /tmp/jinad:/tmp/jinad \
    -p 8000:8000 -d jinaai/jina:test-daemon
"""

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version


def test_create_custom_container():
    workspace_id = create_workspace(
        filepaths=[os.path.join(cur_dir, '../../daemon/unit/models/good_ws/.jinad')]
    )
    assert wait_for_workspace(workspace_id)

    container_id = requests.get(
        f'http://{CLOUD_HOST}/workspaces/{workspace_id}'
    ).json()['metadata']['container_id']
    assert container_id
    container = docker.from_env().containers.get(container_id)
    assert container.name == workspace_id

    workspace_id = create_workspace(
        dirpath=os.path.join(cur_dir, 'custom_workspace_no_run')
    )
    assert wait_for_workspace(workspace_id)
    container_id = requests.get(
        f'http://{CLOUD_HOST}/workspaces/{workspace_id}'
    ).json()['metadata']['container_id']
    assert not container_id


def test_update_custom_container():
    workspace_id = create_workspace(
        filepaths=[
            os.path.join(cur_dir, '../../daemon/unit/models/good_ws/.jinad'),
            os.path.join(cur_dir, 'flow_app_ws/requirements.txt'),
        ]
    )
    assert wait_for_workspace(workspace_id)

    container_id, requirements, image_id = _container_info(workspace_id)
    assert container_id
    assert len(requirements) == 2
    assert image_id

    from contextlib import ExitStack

    with ExitStack() as file_stack:
        requests.put(
            f'http://{CLOUD_HOST}/workspaces/{workspace_id}',
            files=[
                (
                    'files',
                    file_stack.enter_context(
                        open(f'{cur_dir}/tf_encoder_ws/requirements.txt', 'rb')
                    ),
                )
            ],
        )
        assert wait_for_workspace(workspace_id)
        new_container_id, requirements, new_image_id = _container_info(workspace_id)
        assert new_container_id
        assert new_container_id != container_id
        assert new_image_id
        assert new_image_id != image_id
        assert len(requirements) == 3


def _container_info(workspace_id):
    response = requests.get(f'http://{CLOUD_HOST}/workspaces/{workspace_id}').json()
    return (
        response['metadata']['container_id'],
        (response['arguments']['requirements']).split(),
        response['metadata']['image_id'],
    )


def test_delete_custom_container():
    workspace_id = create_workspace(
        dirpath=os.path.join(cur_dir, 'custom_workspace_blocking')
    )
    assert wait_for_workspace(workspace_id)

    # check that container was created
    response = requests.get(f'http://{CLOUD_HOST}/workspaces/{workspace_id}')
    container_id = response.json()['metadata']['container_id']
    assert container_id

    # delete container
    requests.delete(
        f'http://{CLOUD_HOST}/workspaces/{workspace_id}',
        params={
            'container': True,
            'everything': False,
            'network': False,
            'files': False,
        },
    )

    # check that deleted container is gone
    response = requests.get(f'http://{CLOUD_HOST}/workspaces/{workspace_id}')
    assert response.status_code == 200
    container_id = response.json()['metadata']['container_id']
    assert not container_id
