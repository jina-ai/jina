import os

import pytest

from daemon.models import DaemonID, PeaModel, PodModel
from daemon.stores import PeaStore, PodStore
from jina import Executor

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='module', autouse=True)
def workspace():
    from tests.conftest import _create_workspace_directly, _clean_up_workspace

    image_id, network_id, workspace_id, workspace_store = _create_workspace_directly(
        cur_dir
    )
    yield workspace_id
    _clean_up_workspace(image_id, network_id, workspace_id, workspace_store)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'model, store, id',
    [
        (PeaModel(), PeaStore, DaemonID(f'jpea')),
        (PodModel(), PodStore, DaemonID(f'jpod')),
    ],
)
async def test_peapod_store_add(model, store, id, workspace):
    s = store()
    await s.add(id=id, params=model, workspace_id=workspace, ports={})
    assert len(s) == 1
    assert id in s
    await s.delete(id)
    assert not s


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'model, store, type', [(PeaModel(), PeaStore, 'pea'), (PodModel(), PodStore, 'pod')]
)
async def test_peapod_store_multi_add(model, store, type, workspace):
    s = store()
    for j in range(5):
        id = DaemonID(f'j{type}')
        await s.add(id=id, params=model, workspace_id=workspace, ports={})

        assert len(s) == j + 1
        assert id in s
    await s.clear()
    assert not s


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'model, store, id',
    [
        (PeaModel(), PeaStore, DaemonID(f'jpea')),
        (PodModel(), PodStore, DaemonID(f'jpod')),
    ],
)
async def test_peapod_store_add_bad(model, store, id, workspace):
    class BadCrafter(Executor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            raise NotImplementedError

    model.uses = 'BadCrafter'
    s = store()
    with pytest.raises(Exception):
        await s.add(id=id, params=model, workspace_id=workspace, ports={})
    assert not s


@pytest.mark.asyncio
async def test_podstore_rolling_update(workspace):
    id = DaemonID('jpod')
    s = PodStore()
    await s.add(id=id, params=PodModel(), workspace_id=workspace, ports={})
    assert len(s) == 1
    assert id in s
    await s.rolling_update(id=id, uses_with={'a': 'b'})
    await s.delete(id)
    assert not s


@pytest.mark.asyncio
async def test_podstore_scale(workspace):
    id = DaemonID('jpod')
    s = PodStore()
    await s.add(
        id=id, params=PodModel(replicas=2, shards=2), workspace_id=workspace, ports={}
    )
    assert len(s) == 1
    assert id in s
    await s.scale(id=id, replicas=3)
    await s.delete(id)
    assert not s
