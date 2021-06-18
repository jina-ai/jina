import os
import shutil

import pytest

from daemon.dockerize import Dockerizer
from daemon.files import DaemonFile
from daemon.helper import get_workspace_path
from daemon.models import DaemonID, PeaModel, PodModel, WorkspaceItem
from daemon.models.enums import WorkspaceState
from daemon.models.workspaces import WorkspaceMetadata, WorkspaceArguments
from daemon.stores import PeaStore, PodStore
from jina import Executor
from jina.parsers import set_pea_parser, set_pod_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='module')
def workspace():
    workspace_id = DaemonID('jworkspace')
    print(workspace_id)
    workdir = get_workspace_path(workspace_id)
    shutil.copytree(cur_dir, workdir)
    from daemon import daemon_logger

    daemon_file = DaemonFile(
        workdir=get_workspace_path(workspace_id), logger=daemon_logger
    )
    image_id = Dockerizer.build(
        workspace_id=workspace_id, daemon_file=daemon_file, logger=daemon_logger
    )
    network_id = Dockerizer.network(workspace_id=workspace_id)
    from daemon.stores import workspace_store

    workspace_store[workspace_id] = WorkspaceItem(
        state=WorkspaceState.ACTIVE,
        metadata=WorkspaceMetadata(
            image_id=image_id,
            image_name=workspace_id.tag,
            network=network_id,
            workdir=workdir,
        ),
        arguments=WorkspaceArguments(
            files=os.listdir(cur_dir), jinad={'a': 'b'}, requirements=''
        ),
    )
    yield workspace_id
    Dockerizer.rm_image(image_id)
    Dockerizer.rm_network(network_id)
    workspace_store.delete(workspace_id, files=False)


@pytest.mark.parametrize(
    'model, store, id',
    [
        (PeaModel(), PeaStore, DaemonID(f'jpea')),
        (PodModel(), PodStore, DaemonID(f'jpod')),
    ],
)
def test_peastore_add(model, store, id, workspace):
    s = store()
    s.add(id=id, params=model, workspace_id=workspace, ports={})
    assert len(s) == 1
    assert id in s
    s.delete(id)
    assert not s


@pytest.mark.parametrize(
    'model, store, type', [(PeaModel(), PeaStore, 'pea'), (PodModel(), PodStore, 'pod')]
)
def test_peastore_multi_add(model, store, type, workspace):
    s = store()
    for j in range(5):
        id = DaemonID(f'j{type}')
        s.add(id=id, params=model, workspace_id=workspace, ports={})

        assert len(s) == j + 1
        assert id in s
    s.clear()
    assert not s


@pytest.mark.parametrize(
    'model, store, id',
    [
        (PeaModel(), PeaStore, DaemonID(f'jpea')),
        (PodModel(), PodStore, DaemonID(f'jpod')),
    ],
)
def test_peapod_store_add_bad(model, store, id, workspace):
    class BadCrafter(Executor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            raise NotImplementedError

    model.uses = 'BadCrafter'
    s = store()
    with pytest.raises(Exception):
        s.add(id=id, params=model, workspace_id=workspace, ports={})
    assert not s
