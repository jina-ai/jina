import os
from contextlib import contextmanager

import pytest

from daemon.clients import JinaDClient
from jina import Document, Client

NUM_DOCS = 10

cur_dir = os.path.dirname(os.path.abspath(__file__))
jinad_client = JinaDClient(host='localhost', port=8000)


@contextmanager
def RemoteFlow(filename, envs):
    flow_id = None
    try:
        workspace_id = jinad_client.workspaces.create(
            paths=[os.path.join(cur_dir, 'envvars_ws2')]
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
def test_remote_flow_local_executors(replicas):
    with RemoteFlow(
        filename='flow_with_env.yml',
        envs={
            'context_var_1': 'val1',
            'context_var_2': 'val2',
            'num_replicas': replicas,
        },
    ):
        resp = Client(host='localhost', port=12345).post(
            on='/',
            inputs=[Document(id=idx) for idx in range(NUM_DOCS)],
            return_results=True,
        )
        for doc in resp[0].data.docs:
            assert doc.tags['key1'] == 'val1'
            assert doc.tags['key2'] == 'val2'
            assert doc.tags['replicas'] == replicas
