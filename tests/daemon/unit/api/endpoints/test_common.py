from pathlib import Path

import pytest

cur_dir = Path(__file__).parent

deps = ['mwu_encoder.py', 'mwu_encoder.yml']


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


@pytest.mark.parametrize('api', ['/peas', '/pods', '/flows', '/workspaces'])
def test_status(api, fastapi_client):
    response = fastapi_client.delete(f'{api}')
    print(response.json())
    assert response.status_code == 200


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
            '/workspaces',
            {
                'files': [
                    ('files', open(str(cur_dir / 'good_flow.yml'), 'rb')),
                ]
            },
        ),
    ],
)
def test_add_same_del_all(api, payload, fastapi_client):
    for _ in range(3):
        # this test the random default_factory
        response = fastapi_client.post(api, **payload)
        print(response.json())
        assert response.status_code == 201
        _id = response.json()

    response = fastapi_client.get(api)
    assert response.status_code == 200
    num_add = response.json()['num_add']

    response = fastapi_client.delete(f'{api}')
    assert response.status_code == 200

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['num_del'] == num_add
    assert response.json()['size'] == 0


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
            {
                'files': {
                    'flow': (
                        'good_flow.yml',
                        open(str(cur_dir / 'good_flow.yml'), 'rb'),
                    ),
                }
            },
        ),
        (
            '/flows',
            {
                'files': {
                    'flow': (
                        'good_flow_jtype.yml',
                        open(str(cur_dir / 'good_flow_jtype.yml'), 'rb'),
                    ),
                }
            },
        ),
        (
            '/workspaces',
            {
                'files': [
                    ('files', open(str(cur_dir / 'good_flow.yml'), 'rb')),
                    ('files', open(str(cur_dir / 'good_flow_dep.yml'), 'rb')),
                ]
            },
        ),
    ],
)
def test_add_success(api, payload, fastapi_client):
    response = fastapi_client.post(api, **payload)
    print(response.json())
    assert response.status_code == 201
    _id = response.json()

    response = fastapi_client.get(api)
    assert response.status_code == 200

    response = fastapi_client.get(f'{api}/{_id}')
    assert response.status_code == 200
    assert 'time_created' in response.json()

    response = fastapi_client.delete(f'{api}/{_id}')
    assert response.status_code == 200

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['size'] == 0


@pytest.mark.parametrize(
    'api, payload',
    [
        ('/peas', {'json': {'name': 'my_pea', 'uses': 'BAD'}}),
        ('/pods', {'json': {'name': 'my_pod', 'uses': 'BAD'}}),
        (
            '/flows',
            {
                'files': {
                    'flow': ('bad_flow.yml', open(str(cur_dir / 'bad_flow.yml'), 'rb'))
                }
            },
        ),
        (
            '/workspaces',
            {'files': [('bad_flow.yml', open(str(cur_dir / 'bad_flow.yml'), 'rb'))]},
        ),
    ],
)
def test_add_fail(api, payload, fastapi_client):
    response = fastapi_client.get(api)
    assert response.status_code == 200
    old_add = response.json()['num_add']
    old_size = response.json()['size']

    response = fastapi_client.post(api, **payload)
    assert response.status_code != 201
    if response.status_code == 400:
        for k in ('body', 'detail'):
            assert k in response.json()

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['num_add'] == old_add
    assert response.json()['size'] == old_size
