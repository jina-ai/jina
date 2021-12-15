import os

import pytest

from daemon.clients import JinaDClient, AsyncJinaDClient
from daemon.models import DaemonID

from jina import __default_host__
from jina.parsers.flow import set_flow_parser


HOST = __default_host__
PORT = 8000
PROTOCOL = 'HTTP'
EXECUTOR_PORT = 9000
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
    workspace_id = jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert jinad_client.flows.alive()
    # create flow
    flow_id = jinad_client.flows.create(workspace_id=workspace_id, filename='flow.yml')
    assert flow_id
    # get flow status
    remote_flow_args = jinad_client.flows.get(DaemonID(flow_id))
    remote_flow_args = remote_flow_args['arguments']['object']['arguments']
    assert remote_flow_args['port_expose'] == EXECUTOR_PORT
    assert remote_flow_args['protocol'] == PROTOCOL
    assert jinad_client.flows.delete(flow_id)
    assert jinad_client.workspaces.delete(workspace_id)


@pytest.mark.asyncio
async def test_remote_jinad_flow_async(flow_args, async_jinad_client):
    workspace_id = await async_jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert await async_jinad_client.flows.alive()
    # create flow
    flow_id = await async_jinad_client.flows.create(
        workspace_id=workspace_id, filename='flow.yml'
    )
    assert flow_id
    # get flow status
    remote_flow_args = await async_jinad_client.flows.get(DaemonID(flow_id))
    remote_flow_args = remote_flow_args['arguments']['object']['arguments']
    assert remote_flow_args['port_expose'] == EXECUTOR_PORT
    assert remote_flow_args['protocol'] == PROTOCOL
    assert await async_jinad_client.flows.delete(flow_id)
    assert await async_jinad_client.workspaces.delete(workspace_id)


@pytest.mark.asyncio
async def test_jinad_flow_arguments(async_jinad_client):
    resp = await async_jinad_client.flows.arguments()
    assert resp
    assert resp['name']['title'] == 'Name'
