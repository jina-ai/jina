import os

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
def pod_args():
    return set_pod_parser().parse_args([])


@pytest.fixture
def jinad_client():
    return JinaDClient(host=HOST, port=PORT)


@pytest.fixture
def async_jinad_client():
    return AsyncJinaDClient(host=HOST, port=PORT)


def test_remote_jinad_pod(pod_args, jinad_client):
    payload = replace_enum_to_str(ArgNamespace.flatten_to_dict(pod_args))

    workspace_id = jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert jinad_client.pods.alive()
    # create pod
    success, pod_id = jinad_client.pods.create(
        workspace_id=workspace_id, payload=payload
    )
    assert success
    # get pod status
    remote_pod_args = jinad_client.pods.get(pod_id)['arguments']['object']['arguments']
    assert remote_pod_args['identity'] == pod_id
    # delete pod
    assert jinad_client.pods.delete(pod_id)
    resp = jinad_client.pods.get(pod_id)
    assert resp == pod_id + ' not found in store'


@pytest.mark.asyncio
async def test_remote_jinad_pod_async(pod_args, async_jinad_client):
    payload = replace_enum_to_str(ArgNamespace.flatten_to_dict(pod_args))

    workspace_id = await async_jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    assert await async_jinad_client.pods.alive()
    # create pod
    success, pod_id = await async_jinad_client.pods.create(
        workspace_id=workspace_id, payload=payload
    )
    assert success
    # get pod status
    resp = await async_jinad_client.pods.get(pod_id)
    remote_pod_args = resp['arguments']['object']['arguments']
    assert remote_pod_args['identity'] == pod_id
    # delete pod
    assert await async_jinad_client.pods.delete(pod_id)
    resp = await async_jinad_client.pods.get(pod_id)
    assert resp == pod_id + ' not found in store'


@pytest.mark.asyncio
async def test_jinad_pod_create_async_given_unprocessable_entity(
    pod_args, async_jinad_client
):
    payload = replace_enum_to_str(ArgNamespace.flatten_to_dict(pod_args))
    payload['pea_role'] = 'RANDOM'  # patch an invalid pea role type

    workspace_id = await async_jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    success, resp = await async_jinad_client.pods.create(
        workspace_id=workspace_id, payload=payload
    )
    assert not success
    assert 'validation error in the payload' in resp


@pytest.mark.asyncio
async def test_jinad_pod_arguments(pod_args, async_jinad_client):
    resp = await async_jinad_client.pods.arguments()
    assert resp
    assert resp['name']['title'] == 'Name'
