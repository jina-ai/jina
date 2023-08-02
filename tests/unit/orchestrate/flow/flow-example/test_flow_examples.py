import os

import pytest

from jina import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def _validate_flow(f):
    graph_dict = f._get_graph_representation()
    addresses = f._get_deployments_addresses()
    for name, pod in f:
        if name != 'gateway':
            for n in pod.needs:
                assert name in graph_dict[n if n != 'gateway' else 'start-gateway']
        else:
            for n in pod.needs:
                assert 'end-gateway' in graph_dict[n]


@pytest.mark.slow
def test_index():
    f = Flow.load_config(
        os.path.join(cur_dir, '../../../yaml/examples/faiss/flow-index.yml')
    )
    with f:
        _validate_flow(f)


def test_query():
    f = Flow.load_config(
        os.path.join(cur_dir, '../../../yaml/examples/faiss/flow-query.yml')
    )
    with f:
        _validate_flow(f)


@pytest.mark.slow
def test_index():
    f = Flow.load_config(
        os.path.join(cur_dir, '../../../yaml/examples/faces/flow-index.yml')
    )
    with f:
        _validate_flow(f)


@pytest.mark.slow
def test_query():
    f = Flow.load_config(
        os.path.join(cur_dir, '../../../yaml/examples/faces/flow-query.yml')
    )
    with f:
        _validate_flow(f)


@pytest.mark.parametrize('override_executor_log_config', [False, True])
def test_custom_logging(monkeypatch, override_executor_log_config):
    monkeypatch.delenv('JINA_LOG_LEVEL', raising=True)  # ignore global env
    log_config_path = os.path.join(cur_dir, '../../../logging/yaml/file.yml')
    f = Flow(log_config=log_config_path)
    if override_executor_log_config:
        f = f.add(log_config='default')
    else:
        f = f.add()

    with f:
        assert f.args.log_config.endswith('logging/yaml/file.yml')
        for name, pod in f:
            print(name, pod)
            if override_executor_log_config and name.startswith('executor'):
                assert pod.args.log_config == 'default'
            else:
                assert pod.args.log_config.endswith('logging/yaml/file.yml')
