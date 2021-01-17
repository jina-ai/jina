import pytest


@pytest.mark.parametrize('api', ['/peas', '/pods'])
def test_args_status(api, fastapi_client):
    response = fastapi_client.get(f'{api}/arguments')
    assert response.status_code == 200
    assert response.json()

    response = fastapi_client.get(f'{api}')
    assert response.status_code == 200
    assert response.json()


@pytest.mark.parametrize('api', ['/peas', '/pods'])
def test_add_success(api, fastapi_client):
    response = fastapi_client.put(api, json={'name': 'my_pod'})
    assert response.status_code == 201
    _id = response.json()

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['num_add'] == 1

    response = fastapi_client.delete(f'{api}/{_id}')
    assert response.status_code == 200

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['num_del'] == 1
    assert response.json()['size'] == 0


@pytest.mark.parametrize('api', ['/peas', '/pods'])
def test_add_fail(api, fastapi_client):
    response = fastapi_client.get(api)
    assert response.status_code == 200
    old_add = response.json()['num_add']
    old_size = response.json()['size']

    response = fastapi_client.put(api, json={'name': 'my_pod', 'uses': 'badUses'})
    assert response.status_code == 400
    for k in ('body', 'detail'):
        assert k in response.json()

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['num_add'] == old_add
    assert response.json()['size'] == old_size
