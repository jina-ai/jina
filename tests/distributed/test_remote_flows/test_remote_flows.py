import os

import pytest

from daemon.clients import JinaDClient, AsyncJinaDClient
from daemon.models import DaemonID

from jina import __default_host__
from jina.parsers.flow import set_flow_parser


HOST = __default_host__
PORT = 8000
PROTOCOL = 'http'
EXECUTOR_PORT_EXPOSE = 9000
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
    os.environ['JINA_PROTOCAL'] = 'http'
    os.environ['JINA_PORT_EXPOSE'] = '9000'

    workspace_id = jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert jinad_client.flows.alive()
    # create flow
    flow_id = jinad_client.flows.create(workspace_id=workspace_id, filename='flow.yml')
    assert flow_id
    # get flow status
    remote_flow_args = jinad_client.flows.get(DaemonID(flow_id))['arguments']['object'][
        'arguments'
    ]
    assert remote_flow_args['port_expose'] == EXECUTOR_PORT_EXPOSE
    assert remote_flow_args['protocol'] == PROTOCOL
    jinad_client.flows.delete(flow_id)


@pytest.mark.asyncio
async def test_jinad_flow_arguments(async_jinad_client):
    resp = await async_jinad_client.flows.arguments()
    assert resp
    assert resp['name']['title'] == 'Name'
