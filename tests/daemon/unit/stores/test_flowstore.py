from pathlib import Path

from daemon.stores import FlowStore
from jina import Flow

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
    store.delete(flow_id)
    assert flow_id not in store
    assert not store
