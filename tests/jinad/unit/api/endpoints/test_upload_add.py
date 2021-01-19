import os
from pathlib import Path

import pytest

cur_dir = Path(__file__).parent

deps = ['mwu_encoder.py', 'mwu_encoder.yml']


@pytest.mark.parametrize('api, payload', [('/peas', 'pea'), ('/pods', 'pod')])
def test_upload_then_add_success(api, payload, fastapi_client):
    response = fastapi_client.post('/upload', files=[('files', open(str(cur_dir / d), 'rb')) for d in deps])
    assert response.status_code == 200
    workspace_id = response.json()

    response = fastapi_client.post(api, json={payload: {'uses': 'mwu_encoder.yml'},
                                              'workspace_id': workspace_id})
    assert response.status_code == 201
    _id = response.json()

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['size'] == 1

    response = fastapi_client.get(f'{api}/{_id}')
    assert response.status_code == 200
    assert 'uptime' in response.json()
    workdir = response.json()['workdir']
    assert os.path.exists(workdir)
    for d in deps:
        assert os.path.exists(os.path.join(workdir, d))

    response = fastapi_client.delete(f'{api}/{_id}')

    assert response.status_code == 200

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['size'] == 0
    assert not os.path.exists(workdir)


def test_upload_then_add_flow_success(fastapi_client):
    response = fastapi_client.post('/upload', files=[('files', open(str(cur_dir / d), 'rb')) for d in deps])
    assert response.status_code == 200
    workspace_id = response.json()

    response = fastapi_client.post('/flows',
                                   files={'flow': ('good_flow.yml', open(str(cur_dir / 'good_flow_dep.yml'), 'rb')),
                                          'workspace_id': (None, workspace_id)})
    assert response.status_code == 201
    _id = response.json()

    response = fastapi_client.get('/flows')
    assert response.status_code == 200
    assert response.json()['size'] == 1

    response = fastapi_client.get(f'/flows/{_id}')
    assert response.status_code == 200
    assert 'uptime' in response.json()
    workdir = response.json()['workdir']
    assert os.path.exists(workdir)
    for d in deps:
        assert os.path.exists(os.path.join(workdir, d))

    response = fastapi_client.delete(f'/flows/{_id}')

    assert response.status_code == 200

    response = fastapi_client.get('/flows')
    assert response.status_code == 200
    assert response.json()['size'] == 0
    assert not os.path.exists(workdir)
