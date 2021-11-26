import os

import pytest

from daemon.clients import JinaDClient
from jina import Flow, Document, Client, __default_host__

CLOUD_HOST = 'localhost:8000'
NUM_DOCS = 10

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize('replicas', [1, 2])
def test_remote_flow_local_executors(mocker, replicas):
    client = JinaDClient(host=__default_host__, port=8000)
    workspace_id = client.workspaces.create(paths=[cur_dir])
    envs = {'key1': 'val1', 'key2': 'val2', 'REPLICAS': replicas}

    flow_yaml = 'flow_with_env.yml'
    response_mock = mocker.Mock()
    flow_id = client.flows.create(
        workspace_id=workspace_id, filename=flow_yaml, envs=envs
    )
    args = client.flows.get(flow_id)['arguments']['object']['arguments']
    resp = Client(
        host=__default_host__,
        port=args['port_expose'],
        protocol=args['protocol'],
    ).post(
        on='/',
        inputs=[Document(id=idx) for idx in range(NUM_DOCS)],
        on_done=response_mock,
        show_progress=True,
        return_results=True,
    )
    for doc in resp[0].data.docs:
        print(doc)
    # response_mock.assert_called()
    # assert client.flows.delete(flow_id)
    #
    # assert client.workspaces.delete(workspace_id)
