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
    return set_pod_parser().parse_args(['--uses-with', '{"foo": "bar"}'])


@pytest.fixture
def jinad_client():
    return JinaDClient(host=HOST, port=PORT)


@pytest.fixture
def async_jinad_client():
    return AsyncJinaDClient(host=HOST, port=PORT)


@pytest.mark.asyncio
async def test_rolloing_update_remote_pod(async_jinad_client, pod_args):
    payload = replace_enum_to_str(ArgNamespace.flatten_to_dict(pod_args))
    workspace_id = await async_jinad_client.workspaces.create(
        paths=[os.path.join(cur_dir, cur_dir)]
    )
    success, pod_id = await async_jinad_client.pods.create(
        workspace_id=workspace_id, payload=payload
    )
    assert success
    await async_jinad_client.pods.rolling_update(
        id=pod_id, uses_with={'foo': 'bar-new', 'dump_path': 'test'}
    )
    # TODO: HOW TO CHECK PEA ARGS IN JINAD? ROLLING UPDATE WON'T CHANGE POD ARGS
    # TODO: PEA_STORE IS EMPTY
    _ = await async_jinad_client.pods.get(pod_id)
    assert async_jinad_client.pods.delete(pod_id)
    assert async_jinad_client.workspaces.delete(workspace_id)
