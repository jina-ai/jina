import os

from jina import Client, Document
from daemon.clients import JinaDClient

import pytest
import requests

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize('port_expose, func', [('12345', 'foo'), (23456, 'bar')])
def test_port_expose_env_var(port_expose, func):
    jinad_client = JinaDClient(host='localhost', port=8000)
    workspace_id = jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, 'envvars_ws')]
    )
    flow_id = jinad_client.flows.create(
        workspace_id=workspace_id,
        filename='flow.yml',
        envs={'PORT_EXPOSE': port_expose, 'FUNC': func},
    )

    r = Client(host='localhost', port=port_expose, protocol='http').post(
        on='/blah',
        inputs=(Document(text=f'text {i}') for i in range(2)),
        return_results=True,
    )
    for d in r[0].data.docs:
        assert d.text.endswith(func)
    r = requests.get(f'http://localhost:{port_expose}/status')
    assert r.status_code == 200
    envs = r.json()['envs']
    assert envs['JINA_LOG_WORKSPACE'] == '/workspace/logs'
    assert envs['JINA_HUB_CACHE_DIR'] == '/workspace/.cache/jina'
    assert envs['JINA_HUB_ROOT'] == '/workspace/.jina/hub-packages'
    assert jinad_client.flows.delete(flow_id)
    assert jinad_client.workspaces.delete(workspace_id)
