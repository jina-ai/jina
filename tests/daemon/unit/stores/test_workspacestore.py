import os

import pytest
from fastapi import UploadFile

from daemon.stores import WorkspaceStore


@pytest.fixture(scope='function')
def filepath(tmpdir):
    temp_filepath = os.path.join(tmpdir, 'input_file.csv')
    with open(temp_filepath, 'w') as file:
        file.write('hello')
    return temp_filepath


def test_workspace_store(filepath):
    store = WorkspaceStore()
    workspace_id = store.add(files=[UploadFile(filepath)])

    assert store.status.size == 1
    assert store.status.num_add == 1
    assert len(list(store.status.items.values())[0].arguments.files) == 1

    store.delete(workspace_id)

    assert store.status.num_add == 1
    assert store.status.num_del == 1
    assert store.status.size == 0
