import os
import time

import pytest

from daemon.clients import AsyncJinaDClient, JinaDClient
from jina import Client, Document, DocumentArray, __default_host__

cur_dir = os.path.dirname(os.path.abspath(__file__))
IMG_NAME = 'jina/scalable-executor'
HOST = __default_host__
PORT = 8000
FLOW_PORT = 9000
SCALE_EXECUTOR = 'scale_executor'


@pytest.fixture
def pod_params(request):
    replicas, scale_to, shards = request.param
    return replicas, scale_to, shards


@pytest.fixture
def jinad_client():
    return JinaDClient(host=HOST, port=PORT)


@pytest.fixture
def async_jinad_client():
    return AsyncJinaDClient(host=HOST, port=PORT)


@pytest.fixture
def docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(
        path=os.path.join(cur_dir, 'executors/scalable_executor'),
        tag=IMG_NAME,
    )
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.mark.parametrize(
    'pod_params',
    [(1, 2, 1), (2, 3, 1), (3, 1, 1), (1, 2, 2), (2, 1, 2)],
    indirect=True,  # (replicas, scale_to, shards)
)
def test_scale_remote_flow(docker_image_built, jinad_client, pod_params):
    replicas, scale_to, shards = pod_params
    workspace_id = jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert workspace_id
    flow_id = jinad_client.flows.create(
        workspace_id=workspace_id,
        filename='flow-scalable.yml',
        envs={'num_shards': str(shards), 'num_replicas': str(replicas)},
    )
    assert flow_id

    ret1 = Client(host=HOST, port=FLOW_PORT, protocol='http', asyncio=False).index(
        inputs=DocumentArray([Document() for _ in range(200)]),
        return_results=True,
        request_size=10,
    )

    replica_ids = set()
    for r in ret1:
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert len(set(replica_ids)) == replicas

    jinad_client.flows.scale(id=flow_id, pod_name=SCALE_EXECUTOR, replicas=scale_to)

    ret2 = Client(host=HOST, port=FLOW_PORT, protocol='http', asyncio=False).index(
        inputs=DocumentArray([Document() for _ in range(200)]),
        return_results=True,
        request_size=10,
    )

    replica_ids = set()
    for r in ret2:
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert len(set(replica_ids)) == scale_to
    assert jinad_client.flows.delete(flow_id)
    assert jinad_client.workspaces.delete(workspace_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'pod_params',
    [(1, 2, 1), (2, 3, 1), (3, 1, 1), (1, 2, 2), (2, 1, 2)],
    indirect=True,  # (replicas, scale_to, shards)
)
async def test_scale_remote_flow_async(
    docker_image_built, async_jinad_client, pod_params
):
    replicas, scale_to, shards = pod_params
    workspace_id = await async_jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert workspace_id
    flow_id = await async_jinad_client.flows.create(
        workspace_id=workspace_id,
        filename='flow-scalable.yml',
        envs={'num_shards': str(shards), 'num_replicas': str(replicas)},
    )
    assert flow_id

    ret1 = Client(host=HOST, port=FLOW_PORT, protocol='http', asyncio=True).index(
        inputs=DocumentArray([Document() for _ in range(200)]),
        return_results=True,
        request_size=10,
    )

    replica_ids = set()
    async for r in ret1:
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert len(set(replica_ids)) == replicas

    await async_jinad_client.flows.scale(
        id=flow_id, pod_name=SCALE_EXECUTOR, replicas=scale_to
    )

    ret2 = Client(host=HOST, port=FLOW_PORT, protocol='http', asyncio=True).index(
        inputs=DocumentArray([Document() for _ in range(200)]),
        return_results=True,
        request_size=10,
    )

    replica_ids = set()
    async for r in ret2:
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert len(set(replica_ids)) == scale_to
    assert await async_jinad_client.flows.delete(flow_id)
    assert await async_jinad_client.workspaces.delete(workspace_id)
