import os
import shutil

import pytest

from daemon import daemon_logger, __dockerhost__
from daemon.files import DaemonFile
from daemon.models.id import DaemonID
from daemon.dockerize import Dockerizer
from daemon.helper import get_workspace_path
from daemon.models.enums import WorkspaceState
from daemon.models.workspaces import (
    WorkspaceArguments,
    WorkspaceItem,
    WorkspaceMetadata,
)
from daemon.models.containers import ContainerItem

cur_dir = os.path.dirname(os.path.abspath(__file__))

deps = ['mwu_encoder.py', 'mwu_encoder.yml']


@pytest.fixture(scope='module', autouse=True)
def workspace():
    workspace_id = DaemonID('jworkspace')
    print(workspace_id)
    workdir = get_workspace_path(workspace_id)
    shutil.copytree(cur_dir, workdir)
    daemon_file = DaemonFile(
        workdir=get_workspace_path(workspace_id), logger=daemon_logger
    )
    image_id = Dockerizer.build(
        workspace_id=workspace_id, daemon_file=daemon_file, logger=daemon_logger
    )
    network_id = Dockerizer.network(workspace_id=workspace_id)
    from daemon.stores import workspace_store

    workspace_store[workspace_id] = WorkspaceItem(
        state=WorkspaceState.ACTIVE,
        metadata=WorkspaceMetadata(
            image_id=image_id,
            image_name=workspace_id.tag,
            network=network_id,
            workdir=workdir,
        ),
        arguments=WorkspaceArguments(
            files=os.listdir(cur_dir), jinad={'a': 'b'}, requirements=''
        ),
    )
    yield workspace_id
    Dockerizer.rm_image(image_id)
    Dockerizer.rm_network(network_id)
    workspace_store.delete(workspace_id, files=False)


@pytest.mark.parametrize('api', ['/peas', '/pods', '/flows'])
def test_args(api, fastapi_client):
    response = fastapi_client.get(f'{api}/arguments')
    assert response.status_code == 200
    assert response.json()


@pytest.mark.parametrize('api', ['/peas', '/pods', '/flows', '/workspaces'])
def test_status(api, fastapi_client):
    response = fastapi_client.get(f'{api}')
    assert response.status_code == 200
    assert response.json()


@pytest.mark.parametrize('api', ['/peas', '/pods', '/flows'])
def test_delete(api, fastapi_client):
    response = fastapi_client.delete(f'{api}')
    assert response.status_code == 200


def _validate_response(response, payload, id, workspace_id):
    assert response.status_code == 200
    get_response = response.json()
    print(f'\n\n{get_response}')
    item = ContainerItem(**get_response)
    assert item.workspace_id == workspace_id
    assert item.metadata.container_name == id
    assert __dockerhost__ in item.metadata.host

    if 'json' in payload:
        assert item.arguments.object['arguments']['name'] == payload['json']['name']


@pytest.mark.parametrize(
    'api, payload',
    [
        (
            '/peas',
            {
                'json': {'name': 'my_pea'},
            },
        ),
        (
            '/pods',
            {
                'json': {'name': 'my_pod'},
            },
        ),
    ],
)
def test_add_same_del_all(api, payload, fastapi_client, workspace):
    _existing_containers = Dockerizer.containers
    for _ in range(3):
        # this test the random default_factory
        payload['params'] = {'workspace_id': workspace}
        post_response = fastapi_client.post(api, **payload)
        assert post_response.status_code == 201
        obj_id = post_response.json()
        assert obj_id in Dockerizer.containers

        r = fastapi_client.get(f'{api}/{obj_id}')
        _validate_response(r, payload, obj_id, workspace)

    response = fastapi_client.get(api)
    assert response.status_code == 200
    num_add = response.json()['num_add']

    response = fastapi_client.delete(api)
    assert response.status_code == 200

    assert Dockerizer.containers == _existing_containers
    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['num_del'] == num_add


@pytest.mark.parametrize(
    'api, payload',
    [
        (
            '/peas',
            {
                'json': {'name': 'my_pea'},
            },
        ),
        (
            '/pods',
            {
                'json': {'name': 'my_pod'},
            },
        ),
        (
            '/flows',
            {'params': {'filename': 'good_flow.yml'}},
        ),
        (
            '/flows',
            {'params': {'filename': 'good_flow_jtype.yml'}},
        ),
    ],
)
def test_add_success(api, payload, fastapi_client, workspace):
    if 'params' not in payload:
        payload['params'] = {'workspace_id': workspace}
    else:
        payload['params'].update({'workspace_id': workspace})
    post_response = fastapi_client.post(api, **payload)
    assert post_response.status_code == 201
    obj_id = post_response.json()

    assert obj_id in Dockerizer.containers

    r = fastapi_client.get(f'{api}/{obj_id}')
    _validate_response(r, payload, obj_id, workspace)

    response = fastapi_client.get(api)
    assert response.status_code == 200

    response = fastapi_client.get(f'{api}/{obj_id}')
    assert response.status_code == 200
    assert 'time_created' in response.json()

    response = fastapi_client.delete(f'{api}/{obj_id}')
    assert response.status_code == 200

    response = fastapi_client.get(api)
    assert response.status_code == 200


@pytest.mark.parametrize(
    'api, payload',
    [
        ('/peas', {'json': {'name': 'my_pea', 'uses': 'BAD'}}),
        ('/pods', {'json': {'name': 'my_pod', 'uses': 'BAD'}}),
        (
            '/flows',
            {'params': {'filename': 'bad_flow.yml'}},
        ),
    ],
)
def test_add_fail(api, payload, fastapi_client, workspace):
    if 'params' not in payload:
        payload['params'] = {'workspace_id': workspace}
    else:
        payload['params'].update({'workspace_id': workspace})
    response = fastapi_client.get(api)
    assert response.status_code == 200
    old_add = response.json()['num_add']

    response = fastapi_client.post(api, **payload)
    assert response.status_code != 201
    if response.status_code == 400:
        for k in ('body', 'detail'):
            assert k in response.json()

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['num_add'] == old_add
