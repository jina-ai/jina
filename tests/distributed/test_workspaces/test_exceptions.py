import os

import pytest

from daemon.clients import AsyncJinaDClient
from jina import __default_host__

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.asyncio
async def test_flow_error_in_partial_daemon():
    client = AsyncJinaDClient(host=__default_host__, port=8000)
    workspace_id = await client.workspaces.create(
        paths=[os.path.join(cur_dir, 'wrong_flow.yml')]
    )
    error_msg = await client.flows.create(
        workspace_id=workspace_id, filename='wrong_flow.yml'
    )
    assert 'jina.excepts.RuntimeFailToStart' in error_msg
    assert 'jina.excepts.ExecutorFailToLoad' in error_msg
    assert 'FileNotFoundError: can not find executor_ex.yml' in error_msg
    assert await client.workspaces.delete(id=workspace_id)


@pytest.mark.asyncio
async def test_pea_error_in_partial_daemon():
    client = AsyncJinaDClient(host=__default_host__, port=8000)
    workspace_id = await client.workspaces.create()
    error_msg = await client.peas.create(
        workspace_id=workspace_id,
        payload={'name': 'blah-pea', 'py_modules': ['abc.py']},
    )
    assert 'jina.excepts.RuntimeFailToStart' in error_msg
    assert 'FileNotFoundError: can not find abc.py' in error_msg
    assert await client.workspaces.delete(id=workspace_id)
