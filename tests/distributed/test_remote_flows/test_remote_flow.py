import os
import time
import asyncio

import pytest

from daemon.clients import AsyncJinaDClient, JinaDClient
from daemon.models import DaemonID
from jina import Client, Document, __default_host__

HOST = __default_host__
PORT = 8000
PROTOCOL = 'HTTP'
NUM_DOCS = 10
MINI_FLOW1_PORT = 9000
MINI_FLOW2_PORT = 9001
CONTAINER_FLOW_PORT = 9007
cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def flow_envs(request):
    shards, replicas = request.param
    os.environ['num_shards'] = str(shards)
    os.environ['num_replicas'] = str(replicas)
    yield shards, replicas
    del os.environ['num_shards']
    del os.environ['num_replicas']


@pytest.fixture
def jinad_client():
    return JinaDClient(host=HOST, port=PORT)


@pytest.fixture
def async_jinad_client():
    return AsyncJinaDClient(host=HOST, port=PORT)


@pytest.fixture(autouse=True)
async def slow_down_tests():
    yield
    await asyncio.sleep(0.5)


@pytest.fixture
def executor_image():
    import docker

    client = docker.from_env()

    container_image_dir = os.path.join(cur_dir, 'executors', 'container_executor')
    client.images.build(path=container_image_dir, tag='container-executor')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()
    client.close()


@pytest.mark.parametrize('flow_envs', [(1, 1), (2, 1), (2, 2), (1, 2)], indirect=True)
def test_remote_jinad_flow(jinad_client, flow_envs):
    shards, replicas = flow_envs
    workspace_id = jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert jinad_client.flows.alive()
    # create flow
    flow_id = jinad_client.flows.create(
        workspace_id=workspace_id,
        filename='flow1.yml',
        envs={'num_shards': shards, 'num_replicas': replicas},
    )
    assert flow_id
    # get flow status
    remote_flow_args = jinad_client.flows.get(DaemonID(flow_id))
    remote_flow_args = remote_flow_args['arguments']['object']['arguments']
    assert remote_flow_args['port_expose'] == MINI_FLOW1_PORT
    assert remote_flow_args['protocol'] == PROTOCOL
    resp = Client(host=HOST, port=MINI_FLOW1_PORT, protocol='http').post(
        on='/',
        inputs=[Document(id=str(idx)) for idx in range(NUM_DOCS)],
        return_results=True,
    )
    assert len(resp[0].data.docs) == NUM_DOCS
    assert jinad_client.flows.delete(flow_id)
    assert jinad_client.workspaces.delete(workspace_id)


@pytest.mark.asyncio
@pytest.mark.parametrize('flow_envs', [(1, 1), (2, 1), (2, 2), (1, 2)], indirect=True)
async def test_remote_jinad_flow_async(async_jinad_client, flow_envs):
    replicas, shards = flow_envs
    workspace_id = await async_jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert await async_jinad_client.flows.alive()
    # create flow
    flow_id = await async_jinad_client.flows.create(
        workspace_id=workspace_id,
        filename='flow1.yml',
        envs={'num_shards': shards, 'num_replicas': replicas},
    )
    assert flow_id
    # get flow status
    remote_flow_args = await async_jinad_client.flows.get(DaemonID(flow_id))
    remote_flow_args = remote_flow_args['arguments']['object']['arguments']
    assert remote_flow_args['port_expose'] == MINI_FLOW1_PORT
    assert remote_flow_args['protocol'] == PROTOCOL
    resp = Client(host=HOST, port=MINI_FLOW1_PORT, protocol='http', asyncio=True).post(
        on='/',
        inputs=[Document(id=str(idx)) for idx in range(NUM_DOCS)],
        return_results=True,
    )
    async for item in resp:
        assert len(item.data.docs) == NUM_DOCS
    resp = Client(host=HOST, port=MINI_FLOW2_PORT, protocol='http', asyncio=True).post(
        on='/',
        inputs=[Document(id=str(idx)) for idx in range(NUM_DOCS)],
        return_results=True,
    )
    async for item in resp:
        assert len(item.data.docs) == NUM_DOCS
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
        workspace_id=workspace_id,
        filename='flow1.yml',
        envs={'num_shards': 1, 'num_replicas': 1},
    )
    assert flow_id1
    flow_id2 = await async_jinad_client.flows.create(
        workspace_id=workspace_id, filename='flow2.yml'
    )
    assert flow_id2
    # get all flows
    remote_flow_args = await async_jinad_client.flows.list()
    assert len(remote_flow_args.keys()) == 2
    resp = Client(host=HOST, port=MINI_FLOW1_PORT, protocol='http', asyncio=True).post(
        on='/',
        inputs=[Document(id=str(idx)) for idx in range(NUM_DOCS)],
        return_results=True,
    )
    async for item in resp:
        assert len(item.data.docs) == NUM_DOCS
    await async_jinad_client.flows.clear()
    remote_flow_args = await async_jinad_client.flows.list()
    assert len(remote_flow_args.keys()) == 0


@pytest.mark.asyncio
async def test_jinad_flow_arguments(async_jinad_client):
    resp = await async_jinad_client.flows.arguments()
    assert resp
    assert resp['name']['title'] == 'Name'


@pytest.mark.asyncio
async def test_jinad_flow_container_runtime(async_jinad_client, executor_image):
    workspace_id = await async_jinad_client.workspaces.create(paths=[cur_dir])
    flow_id = await async_jinad_client.flows.create(
        workspace_id=workspace_id,
        filename='flow-container.yml',
    )
    assert flow_id
    remote_flow_args = await async_jinad_client.flows.get(DaemonID(flow_id))
    assert remote_flow_args
    resp = Client(
        host=HOST, port=CONTAINER_FLOW_PORT, protocol='http', asyncio=True
    ).post(
        on='/',
        inputs=[Document(id=str(idx)) for idx in range(NUM_DOCS)],
        return_results=True,
    )
    async for item in resp:
        assert len(item.data.docs) == NUM_DOCS
    assert await async_jinad_client.flows.delete(flow_id)
    assert await async_jinad_client.workspaces.delete(workspace_id)
