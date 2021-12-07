import os

import pytest

from daemon.clients import JinaDClient, AsyncJinaDClient

from jina.helper import ArgNamespace
from jina.parsers import set_pod_parser
from jina.enums import replace_enum_to_str


HOST = ''
PORT_JINAD = 8000
cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def pod_args():
    return set_pod_parser().parse_args([])


@pytest.fixture
def jinad_client():
    return JinaDClient(host=HOST, port=PORT_JINAD)


@pytest.fixture
def async_jinad_client():
    return AsyncJinaDClient(host=HOST, port=PORT_JINAD)


def test_jinad_pod_create(pod_args, jinad_client):
    payload = replace_enum_to_str(ArgNamespace.flatten_to_dict(pod_args))

    workspace_id = jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    success, resp = jinad_client.pods.create(workspace_id=workspace_id, payload=payload)
    assert success


@pytest.mark.asyncio
async def test_jinad_pod_create_async(pod_args, async_jinad_client):
    payload = replace_enum_to_str(ArgNamespace.flatten_to_dict(pod_args))

    workspace_id = await async_jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    success, resp = await async_jinad_client.pods.create(
        workspace_id=workspace_id, payload=payload
    )
    assert success


@pytest.mark.asyncio
async def test_jinad_pod_create_async_given_unprocessable_entity(
    pod_args, async_jinad_client
):
    payload = replace_enum_to_str(ArgNamespace.flatten_to_dict(pod_args))

    workspace_id = await async_jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    success, resp = await async_jinad_client.pods.create(
        workspace_id=workspace_id, payload=payload
    )
    assert not success
    assert 'validation error in the payload' in resp
