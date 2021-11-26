import os
from contextlib import contextmanager

import pytest

from daemon.clients import JinaDClient
from jina import Document, Client, __default_host__

CLOUD_HOST = 'localhost:8000'
NUM_DOCS = 10

cur_dir = os.path.dirname(os.path.abspath(__file__))
jinad_client = JinaDClient(host=__default_host__, port=8000)


@contextmanager
def RemoteFlow(filename, envs):
    flow_id = None
    try:
        workspace_id = jinad_client.workspaces.create(paths=[cur_dir])
        print(f'\n\n{workspace_id}\n\n')
        flow_id = jinad_client.flows.create(
            workspace_id=workspace_id, filename=filename, envs=envs
        )
        yield
    finally:
        if flow_id:
            assert jinad_client.flows.delete(flow_id), 'Flow termination failed'
            print(f'Remote Flow {flow_id} successfully terminated')


@pytest.mark.parametrize('replicas', [1])
def test_remote_flow_local_executors(replicas):
    with RemoteFlow(
        filename='flow_with_env.yml',
        envs={'key1': 'val1', 'key2': 'val2', 'REPLICAS': replicas},
    ):
        resp = Client(port=12345).post(
            on='/',
            inputs=[Document(id=idx) for idx in range(NUM_DOCS)],
            return_results=True,
        )
        for doc in resp[0].data.docs:
            print(doc)
        # assert resp[0].data.docs[0].text == directory * mul
