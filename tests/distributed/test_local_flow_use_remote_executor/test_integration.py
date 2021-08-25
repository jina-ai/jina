import os

import pytest
import numpy as np

from jina import Flow, Document
from jina.parsers import set_pod_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))
single_compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
parallel_compose_yml = os.path.join(cur_dir, 'docker-compose-parallel.yml')


@pytest.fixture
def external_pod_args():
    args = ['--port-in', str(45678), '--port-out', str(45679)]
    args = vars(set_pod_parser().parse_args(args))
    del args['external']
    del args['pod_role']
    del args['host']
    del args['dynamic_routing']
    return args


@pytest.fixture
def local_flow(external_pod_args):
    return Flow().add(**external_pod_args, host='10.1.0.100', external=True)


@pytest.fixture
def documents_to_index():
    image = np.random.random((50, 50))
    return [Document(content=image) for i in range(200)]


@pytest.fixture
def patched_remote_local_connection(monkeypatch):
    def alternative_remote_local_connection(first, second):
        if first == '10.1.0.100':
            return True
        else:
            return False

    monkeypatch.setattr(
        'jina.flow.base.is_remote_local_connection',
        lambda x, y: alternative_remote_local_connection(x, y),
    )


@pytest.mark.parametrize(
    'docker_compose',
    [single_compose_yml, parallel_compose_yml],
    indirect=['docker_compose'],
)
def test_local_flow_use_external_executor(
    local_flow, documents_to_index, patched_remote_local_connection, docker_compose
):
    with local_flow as f:
        responses = f.index(
            inputs=documents_to_index, return_results=True, request_size=100
        )
        assert len(responses) == 2
        for resp in responses:
            assert len(resp.docs) == 100
