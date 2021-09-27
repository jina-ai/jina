import os
import pytest
import asyncio

from jina import __default_host__
from daemon.clients import AsyncJinaDClient


cur_dir = os.path.dirname(os.path.abspath(__file__))

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
success = 0
failure = 0

client = AsyncJinaDClient(host=__default_host__, port=8000)


async def get_alive():
    global success, failure
    while True:
        is_alive = await client.alive
        if is_alive:
            success += 1
        else:
            failure += 1


@pytest.mark.asyncio
async def test_nonblocking_server():
    workspace_id = await client.workspaces.create(
        paths=[os.path.join(cur_dir, 'delayed_flow')]
    )

    alive_task = asyncio.create_task(get_alive())
    create_flow_task = asyncio.create_task(
        client.flows.create(workspace_id=workspace_id, filename='delayed_flow.yml')
    )
    done, pending = await asyncio.wait(
        {alive_task, create_flow_task}, return_when=asyncio.FIRST_COMPLETED
    )
    assert create_flow_task in done
    flow_id = create_flow_task.result()
    assert alive_task in pending
    alive_task.cancel()

    await client.flows.delete(flow_id)
    await client.workspaces.delete(workspace_id)
    assert success > 0, f'#success is {success} (expected >0)'
    assert failure == 0, f'#failure is {failure} (expected =0)'
