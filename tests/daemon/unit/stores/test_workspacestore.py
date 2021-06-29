import os

import pytest

from daemon.models import DaemonID
from daemon.stores import WorkspaceStore
from jina.enums import RemoteWorkspaceState


@pytest.fixture(scope='function')
def filepath(tmpdir):
    temp_filepath = os.path.join(tmpdir, 'input_file.csv')
    with open(temp_filepath, 'w') as file:
        file.write('hello')
    return temp_filepath


def test_workspace_store(filepath):
    store = WorkspaceStore()
    id = DaemonID('jworkspace')
    store.add(id=id, value=RemoteWorkspaceState('CREATING'))

    assert len(store) == 1
    assert store.status.num_add == 1
    assert store[id].state == 'CREATING'

    store.delete(id, everything=True)

    assert store.status.num_add == 1
    assert store.status.num_del == 1
    assert len(store) == 0
