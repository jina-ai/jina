import os
from contextlib import contextmanager

import pytest
import requests

from daemon.clients import JinaDClient
from jina import Client, Document, __default_host__

NUM_DOCS = 10
HOST = __default_host__
PORT = 8000
FLOW_PORT = 12345
cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def jinad_client():
    return JinaDClient(host=HOST, port=PORT)


@contextmanager
def RemoteFlow(filename, envs, jinad_client):
    flow_id = None
    try:
        workspace_id = jinad_client.workspaces.create(
            paths=[os.path.join(cur_dir, 'executors', 'envvars_ws2')]
        )
        flow_id = jinad_client.flows.create(
            workspace_id=workspace_id, filename=filename, envs=envs
        )
        yield
    finally:
        if flow_id:
            assert jinad_client.flows.delete(flow_id), 'Flow termination failed'
            print(f'Remote Flow {flow_id} successfully terminated')


@pytest.mark.parametrize('replicas', ['1', '2'])
def test_remote_flow_local_executors(replicas, jinad_client):
    with RemoteFlow(
        filename='flow_with_env.yml',
        envs={
            'context_var_1': 'val1',
            'context_var_2': 'val2',
            'num_replicas': replicas,
        },
        jinad_client=jinad_client,
    ):
        resp = Client(host=HOST, port=FLOW_PORT).post(
            on='/',
            inputs=[Document(id=str(idx)) for idx in range(NUM_DOCS)],
            return_results=True,
        )
        for doc in resp[0].data.docs:
            assert doc.tags['key1'] == 'val1'
            assert doc.tags['key2'] == 'val2'
            assert doc.tags['replicas'] == replicas


@pytest.mark.parametrize('port_expose, func', [('12345', 'foo'), (23456, 'bar')])
def test_port_expose_env_var(port_expose, func, jinad_client):
    workspace_id = jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, 'executors', 'envvars_ws1')]
    )
    flow_id = jinad_client.flows.create(
        workspace_id=workspace_id,
        filename='flow.yml',
        envs={'PORT_EXPOSE': port_expose, 'FUNC': func},
    )

    r = Client(host=HOST, port=port_expose, protocol='http').post(
        on='/blah',
        inputs=(Document(text=f'text {i}') for i in range(2)),
        return_results=True,
    )
    for d in r[0].data.docs:
        assert d.text.endswith(func)
    r = requests.get(f'http://{HOST}:{port_expose}/status')
    assert r.status_code == 200
    envs = r.json()['envs']
    assert envs['JINA_LOG_WORKSPACE'] == '/workspace/logs'
    assert envs['JINA_HUB_CACHE_DIR'] == '/workspace/.cache/jina'
    assert envs['JINA_HUB_ROOT'] == '/workspace/.jina/hub-packages'
    assert jinad_client.flows.delete(flow_id)
    assert jinad_client.workspaces.delete(workspace_id)
