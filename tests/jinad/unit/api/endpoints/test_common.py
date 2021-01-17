import pytest


@pytest.mark.parametrize('api', ['/peas', '/pods', '/flows'])
def test_args(api, fastapi_client):
    response = fastapi_client.get(f'{api}/arguments')
    assert response.status_code == 200
    assert response.json()


@pytest.mark.parametrize('api', ['/peas', '/pods', '/flows'])
def test_status(api, fastapi_client):
    response = fastapi_client.get(f'{api}')
    assert response.status_code == 200
    assert response.json()


@pytest.mark.parametrize('api, payload', [('/peas', {'json': {'name': 'my_pea'}}),
                                          ('/pods', {'json': {'name': 'my_pod'}}),
                                          ('/flows',
                                           {'files': {'flow': ('good_flow.yml', open('good_flow.yml', 'rb'))}})])
def test_add_success(api, payload, fastapi_client):
    response = fastapi_client.put(api, **payload)
    print(response.json())
    assert response.status_code == 201
    _id = response.json()

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['num_add'] == 1

    response = fastapi_client.get(f'{api}/{_id}')
    assert response.status_code == 200
    assert 'uptime' in response.json()

    response = fastapi_client.delete(f'{api}/{_id}')
    assert response.status_code == 200

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['num_del'] == 1
    assert response.json()['size'] == 0


@pytest.mark.parametrize('api, payload', [('/peas', {'json': {'name': 'my_pea', 'uses': 'BAD'}}),
                                          ('/pods', {'json': {'name': 'my_pod', 'uses': 'BAD'}}),
                                          (
                                                  '/flows',
                                                  {'files': {'flow': ('bad_flow.yml', open('bad_flow.yml', 'rb'))}})])
def test_add_fail(api, payload, fastapi_client):
    response = fastapi_client.get(api)
    assert response.status_code == 200
    old_add = response.json()['num_add']
    old_size = response.json()['size']

    response = fastapi_client.put(api, **payload)
    assert response.status_code == 400
    for k in ('body', 'detail'):
        assert k in response.json()

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['num_add'] == old_add
    assert response.json()['size'] == old_size
