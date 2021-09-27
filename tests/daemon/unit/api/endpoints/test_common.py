import os
import time

import pytest

from daemon.dockerize import Dockerizer
from daemon.models.containers import ContainerItem

cur_dir = os.path.dirname(os.path.abspath(__file__))

deps = ['mwu_encoder.py', 'mwu_encoder.yml']


@pytest.fixture(scope='module', autouse=True)
def workspace():
    from tests.conftest import _create_workspace_directly, _clean_up_workspace

    image_id, network_id, workspace_id, workspace_store = _create_workspace_directly(
        cur_dir
    )
    yield workspace_id
    _clean_up_workspace(image_id, network_id, workspace_id, workspace_store)


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
    item = ContainerItem(**get_response)
    assert item.workspace_id == workspace_id
    assert item.metadata.container_name == id

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

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['num_del'] == num_add
    time.sleep(1)
    assert Dockerizer.containers == _existing_containers


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
