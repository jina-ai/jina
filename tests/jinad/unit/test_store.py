from pathlib import Path

import pytest
from fastapi import UploadFile

from daemon.store import InMemoryPeaStore, InMemoryPodStore, InMemoryFlowStore
from jina.flow import Flow
from jina.parsers import set_pea_parser, set_pod_parser
from jina.peapods.pods import BasePod

cur_dir = Path(__file__).parent


def pod_list_one():
    return [{'name': 'pod1'}]


def pod_list_multiple():
    return [{'name': 'pod1'}, {'name': 'pod2'}]


def flow_file_str():
    with open(str(cur_dir / 'yaml' / 'flow.yml'), 'r') as f:
        config_str = f.read()

    return config_str


@pytest.mark.parametrize('config', [flow_file_str(), pod_list_one(), pod_list_multiple()])
def test_flow_store(config):
    store = InMemoryFlowStore()
    with store.session():
        flow_id, _, _ = store._create(config=config)
        assert flow_id in store._items.keys()
        assert isinstance(store._items[flow_id]['flow'], Flow)
        store._delete(flow_id)
        assert flow_id not in store._items.keys()


def test_flow_store_with_files(tmpdir):
    config = flow_file_str()
    file_yml = UploadFile(Path(tmpdir) / 'file1.yml')
    file_py = UploadFile(Path(tmpdir) / 'file1.py')
    files = [file_yml, file_py]
    store = InMemoryFlowStore()
    with store.session():
        flow_id, _, _ = store._create(config=config, files=files)
        assert Path(file_yml.filename).exists()
        assert Path(file_py.filename).exists()
        assert flow_id in store._items.keys()
        assert isinstance(store._items[flow_id]['flow'], Flow)
        store._delete(flow_id)
        assert flow_id not in store._items.keys()
        assert not Path(file_yml.filename).exists()
        assert not Path(file_py.filename).exists()


def test_pod_store():
    args = set_pod_parser().parse_args([])
    store = InMemoryPodStore()
    with store.session():
        pod_id = store._create(pod_arguments=args)
        assert pod_id in store._items.keys()
        assert isinstance(store._items[pod_id]['pod'], BasePod)
        store._delete(pod_id)
        assert pod_id not in store._items.keys()


def test_pea_store():
    args = set_pea_parser().parse_args([])
    store = InMemoryPeaStore()
    with store.session():
        pea_id = store._create(pea_arguments=args)
        assert pea_id in store._items.keys()
        # assert isinstance(store._store[pea_id]['pea'], LocalRuntime)
        store._delete(pea_id)
        assert pea_id not in store._items.keys()
