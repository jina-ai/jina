import os
import asyncio

import pytest

from daemon.clients import JinaDClient, AsyncJinaDClient

from jina import __default_host__
from jina.helper import ArgNamespace
from jina.parsers import set_pod_parser
from jina.enums import replace_enum_to_str

HOST = __default_host__
PORT = 8000
cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def jinad_client():
    return JinaDClient(host=HOST, port=PORT)


@pytest.fixture
def async_jinad_client():
    return AsyncJinaDClient(host=HOST, port=PORT)


@pytest.fixture
async def slow_down_tests():
    yield
    await asyncio.sleep(0.5)


@pytest.mark.parametrize(
    'pod_params',  # (num_replicas, scale_to, shards)
    [
        (2, 3, 1),  # scale up 1 replica with 1 shard
        (2, 3, 2),  # scale up 1 replica with 2 shards
        (3, 1, 1),  # scale down 2 replicas with 1 shard
        (3, 1, 2),  # scale down 2 replicas with 1 shard
    ],
)
def test_scale_remote_pod(pod_params, jinad_client):
    num_replicas, scale_to, shards = pod_params
    args = set_pod_parser().parse_args(
        ['--replicas', str(num_replicas), '--shards', str(shards)]
    )
    payload = replace_enum_to_str(ArgNamespace.flatten_to_dict(args))

    workspace_id = jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    success, pod_id = jinad_client.pods.create(
        workspace_id=workspace_id, payload=payload
    )
    assert success

    remote_pod_args = jinad_client.pods.get(pod_id)['arguments']['object']['arguments']
    assert remote_pod_args['identity'] == pod_id
    assert remote_pod_args['replicas'] == num_replicas
    assert remote_pod_args['shards'] == shards

    jinad_client.pods.scale(id=pod_id, replicas=scale_to)
    remote_pod_args = jinad_client.pods.get(pod_id)['arguments']['object']['arguments']
    assert remote_pod_args['identity'] == pod_id
    assert remote_pod_args['replicas'] == scale_to
    assert remote_pod_args['shards'] == shards
    assert jinad_client.pods.delete(pod_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'pod_params',  # (num_replicas, scale_to, shards)
    [
        (2, 3, 1),  # scale up 1 replica with 1 shard
        (2, 3, 2),  # scale up 1 replica with 2 shards
        (3, 1, 1),  # scale down 2 replicas with 1 shard
        (3, 1, 2),  # scale down 2 replicas with 1 shard
    ],
)
async def test_scale_remote_pod_async(pod_params, async_jinad_client, slow_down_tests):
    num_replicas, scale_to, shards = pod_params
    args = set_pod_parser().parse_args(
        ['--replicas', str(num_replicas), '--shards', str(shards)]
    )
    payload = replace_enum_to_str(ArgNamespace.flatten_to_dict(args))

    workspace_id = await async_jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    success, pod_id = await async_jinad_client.pods.create(
        workspace_id=workspace_id, payload=payload
    )
    assert success

    resp = await async_jinad_client.pods.get(pod_id)
    remote_pod_args = resp['arguments']['object']['arguments']
    assert remote_pod_args['identity'] == pod_id
    assert remote_pod_args['replicas'] == num_replicas
    assert remote_pod_args['shards'] == shards

    await async_jinad_client.pods.scale(id=pod_id, replicas=scale_to)
    resp = await async_jinad_client.pods.get(pod_id)
    remote_pod_args = resp['arguments']['object']['arguments']
    assert remote_pod_args['identity'] == pod_id
    assert remote_pod_args['replicas'] == scale_to
    assert remote_pod_args['shards'] == shards
    assert await async_jinad_client.pods.delete(pod_id)
