import os

import pytest

from daemon.clients import JinaDClient, AsyncJinaDClient

from jina import __default_host__
from jina.helper import ArgNamespace
from jina.enums import replace_enum_to_str
from jina.parsers.flow import set_flow_parser


HOST = __default_host__
PORT = 8000
cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def flow_args():
    return set_flow_parser().parse_args([])


@pytest.fixture
def jinad_client():
    return JinaDClient(host=HOST, port=PORT)


@pytest.fixture
def async_jinad_client():
    return AsyncJinaDClient(host=HOST, port=PORT)


def test_remote_jinad_flow(flow_args, jinad_client):
    payload = replace_enum_to_str(ArgNamespace.flatten_to_dict(flow_args))

    workspace_id = jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert jinad_client.flows.alive()
    # create flow
    success, flow_id = jinad_client.flows.create(workspace_id=workspace_id, filename='')
    assert success
    # get flow status
    remote_pod_args = jinad_client.flows.get(flow_id)['arguments']['object'][
        'arguments'
    ]


@pytest.mark.asyncio
async def test_jinad_flow_arguments(async_jinad_client):
    resp = await async_jinad_client.flows.arguments()
    assert resp
    assert resp['name']['title'] == 'Name'
