from pathlib import Path

from fastapi import UploadFile

from daemon.stores import FlowStore
from jina.flow import Flow

cur_dir = Path(__file__).parent


def pod_list_one():
    return [{'name': 'pod1'}]


def pod_list_multiple():
    return [{'name': 'pod1'}, {'name': 'pod2'}]


def test_flow_store():
    store = FlowStore()
    flow_id = store.add(config=open(str(cur_dir / 'flow.yml'), 'rb'))
    assert len(store) == 1
    assert flow_id in store
    assert isinstance(store[flow_id]['object'], Flow)
    del store[flow_id]
    assert flow_id not in store
    assert not store


def test_flow_store_with_files(tmpdir):
    store = FlowStore()
    results_id = []
    workdirs = []
    num_flow = 2

    for j in range(num_flow):
        deps = ['mwu_encoder.py', 'mwu_encoder.yml']
        dep_files = [UploadFile(cur_dir / d) for d in deps]
        flow_id = store.add(open(str(cur_dir / 'flow.yml'), 'rb'),
                            dep_files)
        assert len(store) == j + 1
        assert flow_id in store
        assert isinstance(store[flow_id]['object'], Flow)
        results_id.append(flow_id)
        workdirs.append(store[flow_id]['workdir'])

    assert len(set(workdirs)) == num_flow
    store.clear()

    for flow_id in results_id:
        assert flow_id not in store
    assert not store
