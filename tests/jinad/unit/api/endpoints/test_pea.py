import pytest
from fastapi.testclient import TestClient

from daemon import _get_app

client = TestClient(_get_app())


def test_args():
    response = client.get('/peas/arguments')
    assert response.status_code == 200
    assert response.json()


@pytest.mark.parametrize('api', ['/peas', '/pods'])
def test_add_success(api):
    response = client.put(api, json={'name': 'my_pod'})
    assert response.status_code == 201
    _id = response.json()

    response = client.get(api)
    assert response.status_code == 200
    assert response.json()['num_add'] == 1

    response = client.delete(f'{api}/{_id}')
    assert response.status_code == 200

    response = client.get(api)
    assert response.status_code == 200
    assert response.json()['num_del'] == 1
    assert response.json()['size'] == 0


@pytest.mark.parametrize('api', ['/peas', '/pods'])
def test_add_fail(api):
    response = client.put(api, json={'name': 'my_pod', 'uses': 'badUses'})
    assert response.status_code == 400
    for k in ('body', 'detail'):
        assert k in response.json()

    response = client.get(api)
    assert response.status_code == 200
    assert response.json()['num_add'] == 0
    assert response.json()['size'] == 0
