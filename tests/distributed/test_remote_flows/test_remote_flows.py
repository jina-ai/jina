import os

import pytest

from daemon.clients import JinaDClient, AsyncJinaDClient
from daemon.models import DaemonID

from jina import __default_host__
from jina.parsers.flow import set_flow_parser


HOST = __default_host__
PORT = 8000
PROTOCOL = 'HTTP'
MINI_FLOW1_PORT = 9000
MINI_FLOW2_PORT = 9001
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


def test_remote_jinad_flow(jinad_client):
    workspace_id = jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert jinad_client.flows.alive()
    # create flow
    flow_id = jinad_client.flows.create(workspace_id=workspace_id, filename='flow1.yml')
    assert flow_id
    # get flow status
    remote_flow_args = jinad_client.flows.get(DaemonID(flow_id))
    remote_flow_args = remote_flow_args['arguments']['object']['arguments']
    assert remote_flow_args['port_expose'] == MINI_FLOW1_PORT
    assert remote_flow_args['protocol'] == PROTOCOL
    assert jinad_client.flows.delete(flow_id)
    assert jinad_client.workspaces.delete(workspace_id)


@pytest.mark.asyncio
async def test_remote_jinad_flow_async(async_jinad_client):
    workspace_id = await async_jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert await async_jinad_client.flows.alive()
    # create flow
    flow_id = await async_jinad_client.flows.create(
        workspace_id=workspace_id, filename='flow1.yml'
    )
    assert flow_id
    # get flow status
    remote_flow_args = await async_jinad_client.flows.get(DaemonID(flow_id))
    remote_flow_args = remote_flow_args['arguments']['object']['arguments']
    assert remote_flow_args['port_expose'] == MINI_FLOW1_PORT
    assert remote_flow_args['protocol'] == PROTOCOL
    assert await async_jinad_client.flows.delete(flow_id)
    assert await async_jinad_client.workspaces.delete(workspace_id)


@pytest.mark.asyncio
async def test_remote_jinad_flow_get_delete_all(async_jinad_client):
    workspace_id = await async_jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert await async_jinad_client.flows.alive()
    # create flow
    flow_id1 = await async_jinad_client.flows.create(
        workspace_id=workspace_id, filename='flow1.yml'
    )
    assert flow_id1
    flow_id2 = await async_jinad_client.flows.create(
        workspace_id=workspace_id, filename='flow2.yml'
    )
    assert flow_id2
    # get all flows
    remote_flow_args = await async_jinad_client.flows.list()
    assert len(remote_flow_args.keys()) == 2
    await async_jinad_client.flows.clear()
    remote_flow_args = await async_jinad_client.flows.list()
    assert len(remote_flow_args.keys()) == 0


@pytest.mark.asyncio
async def test_jinad_flow_arguments(async_jinad_client):
    resp = await async_jinad_client.flows.arguments()
    assert resp
    assert resp['name']['title'] == 'Name'
