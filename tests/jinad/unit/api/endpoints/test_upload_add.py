import os
from pathlib import Path

import pytest

from daemon.stores.helper import get_workspace_path

cur_dir = Path(__file__).parent

deps = ['mwu_encoder.py', 'mwu_encoder.yml']


@pytest.mark.parametrize('api, payload', [('/peas', 'pea'), ('/pods', 'pod')])
def test_upload_then_add_success(api, payload, fastapi_client):
    response = fastapi_client.post('/workspaces', files=[('files', open(str(cur_dir / d), 'rb')) for d in deps])
    assert response.status_code == 201
    workspace_id = response.json()
    assert os.path.exists(get_workspace_path(workspace_id))
    for d in deps:
        assert os.path.exists(get_workspace_path(workspace_id, d))

    response = fastapi_client.post(api, json={'uses': 'mwu_encoder.yml',
                                              'workspace_id': workspace_id,
                                              })
    assert response.status_code == 201
    _id = response.json()

    response = fastapi_client.get(api)
    assert response.status_code == 200
    assert response.json()['size'] == 1

    response = fastapi_client.get(f'{api}/{_id}')
    assert response.status_code == 200
    assert 'time_created' in response.json()
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
    response = fastapi_client.post('/workspaces', files=[('files', open(str(cur_dir / d), 'rb')) for d in deps])
    assert response.status_code == 201
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
    assert 'time_created' in response.json()
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
