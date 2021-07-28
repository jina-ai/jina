import os

import docker
import pytest

from jina import __default_host__
from daemon.clients import JinaDClient
from daemon.models.workspaces import WorkspaceItem

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
    client = JinaDClient(host=__default_host__, port=8000)
    workspace_id = client.workspaces.create(
        paths=[os.path.join(cur_dir, '../../daemon/unit/models/good_ws/.jinad')]
    )
    workspace_details = client.workspaces.get(id=workspace_id)
    workspace_details = WorkspaceItem(**workspace_details)
    assert workspace_details.metadata.container_id

    container = docker.from_env().containers.get(
        workspace_details.metadata.container_id
    )
    assert container.name == workspace_id

    workspace_id = client.workspaces.create(
        paths=[os.path.join(cur_dir, 'custom_workspace_no_run')]
    )
    workspace_details = client.workspaces.get(id=workspace_id)
    workspace_details = WorkspaceItem(**workspace_details)
    assert not workspace_details.metadata.container_id


def test_update_custom_container():
    client = JinaDClient(host=__default_host__, port=8000)
    workspace_id = client.workspaces.create(
        paths=[
            os.path.join(cur_dir, '../../daemon/unit/models/good_ws/.jinad'),
            os.path.join(cur_dir, 'flow_app_ws/requirements.txt'),
        ]
    )
    workspace_details = client.workspaces.get(id=workspace_id)
    workspace_details = WorkspaceItem(**workspace_details)
    container_id = workspace_details.metadata.container_id
    assert container_id
    image_id = workspace_details.metadata.image_id
    assert image_id
    assert len(workspace_details.arguments.requirements.split()) == 2

    workspace_id = client.workspaces.update(
        id=workspace_id,
        paths=[os.path.join(cur_dir, 'sklearn_encoder_ws/requirements.txt')],
    )
    workspace_details = client.workspaces.get(id=workspace_id)
    workspace_details = WorkspaceItem(**workspace_details)
    new_container_id = workspace_details.metadata.container_id
    assert new_container_id
    assert new_container_id != container_id
    new_image_id = workspace_details.metadata.image_id
    assert new_image_id
    assert new_image_id != image_id
    assert len(workspace_details.arguments.requirements.split()) == 3


def test_delete_custom_container():
    client = JinaDClient(host=__default_host__, port=8000)
    workspace_id = client.workspaces.create(
        paths=[
            os.path.join(cur_dir, 'custom_workspace_blocking'),
        ]
    )

    # check that container was created
    workspace_details = client.workspaces.get(id=workspace_id)
    workspace_details = WorkspaceItem(**workspace_details)
    container_id = workspace_details.metadata.container_id
    assert container_id

    client.workspaces.delete(
        id=workspace_id, container=True, network=False, files=False, everything=False
    )
    # check that deleted container is gone
    workspace_details = client.workspaces.get(id=workspace_id)
    workspace_details = WorkspaceItem(**workspace_details)
    container_id = workspace_details.metadata.container_id
    assert not container_id
