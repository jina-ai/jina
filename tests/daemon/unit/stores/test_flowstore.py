import os
import shutil
from pathlib import Path

import pytest

from daemon.dockerize import Dockerizer
from daemon.files import DaemonFile
from daemon.helper import get_workspace_path
from daemon.models import DaemonID, WorkspaceItem, FlowModel
from daemon.models.enums import WorkspaceState
from daemon.models.workspaces import WorkspaceMetadata, WorkspaceArguments
from daemon.stores import FlowStore

cur_dir = Path(__file__).parent


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
    del workspace_store[workspace_id]
    workspace_store.dump(lambda *args, **kwargs: None)


def pod_list_one():
    return [{'name': 'pod1'}]


def pod_list_multiple():
    return [{'name': 'pod1'}, {'name': 'pod2'}]


def test_flow_store(workspace):
    store = FlowStore()
    flow_id = DaemonID('jflow')
    flow_model = FlowModel()
    flow_model.uses = f'flow.yml'

    store.add(id=flow_id, workspace_id=workspace, params=flow_model, ports={})
    assert len(store) == 1
    assert flow_id in store
    store.delete(flow_id)
    assert flow_id not in store
    assert not store
