from pathlib import Path

import pytest

from daemon.models import DaemonID, FlowModel
from daemon.stores import FlowStore

cur_dir = Path(__file__).parent


@pytest.fixture(scope='module', autouse=True)
def workspace():
    from tests.conftest import _create_workspace_directly, _clean_up_workspace

    image_id, network_id, workspace_id, workspace_store = _create_workspace_directly(
        cur_dir
    )
    yield workspace_id
    _clean_up_workspace(image_id, network_id, workspace_id, workspace_store)


def pod_list_one():
    return [{'name': 'executor1'}]


def pod_list_multiple():
    return [{'name': 'executor1'}, {'name': 'executor2'}]


@pytest.mark.asyncio
async def test_flow_store(workspace):
    store = FlowStore()
    flow_id = DaemonID('jflow')
    flow_model = FlowModel()
    flow_model.uses = f'flow.yml'

    await store.add(
        id=flow_id,
        workspace_id=workspace,
        params=flow_model,
        ports={},
        port_expose=56789,
    )
    assert len(store) == 1
    assert flow_id in store
    await store.delete(flow_id)
    assert flow_id not in store
    assert not store


@pytest.mark.asyncio
async def test_flow_store_rolling_update(workspace):
    store = FlowStore()
    flow_id = DaemonID('jflow')
    flow_model = FlowModel()
    flow_model.uses = f'flow.yml'

    await store.add(
        id=flow_id,
        workspace_id=workspace,
        params=flow_model,
        ports={},
        port_expose=56789,
    )
    assert len(store) == 1
    assert flow_id in store
    await store.rolling_update(id=flow_id, pod_name='executor1')
    assert len(store) == 1
    assert flow_id in store
    await store.delete(flow_id)
    assert flow_id not in store
    assert not store


@pytest.mark.asyncio
async def test_flow_store_scale(workspace):
    store = FlowStore()
    flow_id = DaemonID('jflow')
    flow_model = FlowModel()
    flow_model.uses = f'flow.yml'

    await store.add(
        id=flow_id,
        workspace_id=workspace,
        params=flow_model,
        ports={},
        port_expose=56789,
    )
    assert len(store) == 1
    assert flow_id in store
    await store.scale(id=flow_id, pod_name='executor1', replicas=2)
    assert len(store) == 1
    assert flow_id in store
    await store.delete(flow_id)
    assert flow_id not in store
    assert not store
