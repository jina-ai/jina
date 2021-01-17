from pathlib import Path

import pytest
from fastapi import UploadFile

from daemon.stores import FlowStore
from jina.flow import Flow

cur_dir = Path(__file__).parent


def pod_list_one():
    return [{'name': 'pod1'}]


def pod_list_multiple():
    return [{'name': 'pod1'}, {'name': 'pod2'}]


def flow_file_str():
    with open('flow.yml', 'r') as f:
        config_str = f.read()
    return config_str


@pytest.mark.parametrize('config', [flow_file_str(), pod_list_one(), pod_list_multiple()])
def test_flow_store(config):
    store = FlowStore()
    flow_id = store.add(config=config)
    assert len(store) == 1
    assert flow_id in store
    assert isinstance(store[flow_id]['object'], Flow)
    del store[flow_id]
    assert flow_id not in store
    assert not store


def test_flow_store_with_files(tmpdir):
    store = FlowStore()
    results = []
    for j in range(3):
        config = flow_file_str()
        file_yml = UploadFile(Path(tmpdir) / 'file1.yml')
        file_py = UploadFile(Path(tmpdir) / 'file1.py')
        files = [file_yml, file_py]
        flow_id = store.add(config=config, files=files)
        assert len(store) == j + 1
        assert Path(file_yml.filename).exists()
        assert Path(file_py.filename).exists()
        assert flow_id in store
        assert isinstance(store[flow_id]['object'], Flow)
        results.append((flow_id, file_yml, file_py))
    store.clear()

    for flow_id, file_yml, file_py in results:
        assert flow_id not in store
        assert not Path(file_yml.filename).exists()
        assert not Path(file_py.filename).exists()
    assert not store
