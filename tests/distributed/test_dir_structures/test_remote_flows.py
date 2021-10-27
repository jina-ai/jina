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


@pytest.mark.parametrize('directory', (['src1', 'src2', 'src3', 'src4']))
def test_remote_flow_with_config_yaml(directory):
    with RemoteFlow(
        directory=os.path.join(cur_dir, directory),
        filename='flow_config_yml.yml',
        envs={'PORT_EXPOSE': 12345},
    ):
        resp = Client(port=12345).post(
            on='/',
            inputs=Document(text=directory),
            return_results=True,
        )
        assert resp[0].data.docs[0].text == directory * 2


@pytest.mark.parametrize('directory', (['src1', 'src2', 'src3', 'src4']))
def test_remote_flow_with_py_modules(directory):
    with RemoteFlow(
        directory=os.path.join(cur_dir, directory),
        filename='flow_py_modules.yml',
        envs={'PORT_EXPOSE': 12345},
    ):
        resp = Client(port=12345).post(
            on='/',
            inputs=Document(text=directory),
            return_results=True,
        )
        assert resp[0].data.docs[0].text == directory * 2
