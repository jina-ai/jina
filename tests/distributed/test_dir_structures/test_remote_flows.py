import os
from contextlib import contextmanager
from typing import Dict

import pytest

from daemon.clients import JinaDClient
from jina import Client, Document, __default_host__

cur_dir = os.path.dirname(os.path.abspath(__file__))
jinad_client = JinaDClient(host=__default_host__, port=8000)


@contextmanager
def RemoteFlow(directory, filename: str, envs: Dict[str, str] = {}):
    flow_id = None
    try:
        workspace_id = jinad_client.workspaces.create(
            paths=[os.path.join(cur_dir, directory)]
        )
        flow_id = jinad_client.flows.create(
            workspace_id=workspace_id, filename=filename, envs=envs
        )
        yield
    finally:
        if flow_id:
            assert jinad_client.flows.delete(flow_id), 'Flow termination failed'
            print(f'Remote Flow {flow_id} successfully terminated')


@pytest.mark.parametrize('filename', ['flow_config_yml.yml', 'flow_py_modules.yml'])
@pytest.mark.parametrize(
    'directory, mul',
    [('src1', 2), ('src2', 2), ('src3', 2), ('src4', 4), ('src5', 2)],
)
def test_remote_flow_with_directory(directory, filename, mul):
    with RemoteFlow(
        directory=directory,
        filename=filename,
        envs={'PORT_EXPOSE': 12345},
    ):
        resp = Client(port=12345).post(
            on='/',
            inputs=Document(text=directory),
            return_results=True,
        )
        assert resp[0].data.docs[0].text == directory * mul
