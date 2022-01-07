import os

import pytest

from jina import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def _validate_flow(f):
    graph_dict = f._get_graph_representation()
    adresses = f._get_pod_addresses()
    for name, pod in f:
        if name != 'gateway':
            assert adresses[name][0] == f'{pod.host}:{pod.head_port_in}'
            for n in pod.needs:
                assert name in graph_dict[n if n != 'gateway' else 'start-gateway']
        else:
            for n in pod.needs:
                assert 'end-gateway' in graph_dict[n]


@pytest.mark.slow
def test_index():
    f = Flow.load_config(os.path.join(cur_dir, '../yaml/examples/faiss/flow-index.yml'))
    with f:
        _validate_flow(f)


def test_query():
    f = Flow.load_config(os.path.join(cur_dir, '../yaml/examples/faiss/flow-query.yml'))
    with f:
        _validate_flow(f)


@pytest.mark.slow
def test_index():
    f = Flow.load_config(os.path.join(cur_dir, '../yaml/examples/faces/flow-index.yml'))
    with f:
        _validate_flow(f)


@pytest.mark.slow
def test_query():
    f = Flow.load_config(os.path.join(cur_dir, '../yaml/examples/faces/flow-query.yml'))
    with f:
        _validate_flow(f)
