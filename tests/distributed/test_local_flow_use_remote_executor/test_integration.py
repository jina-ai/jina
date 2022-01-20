import os

import pytest
import numpy as np

from jina import Flow, Document, Client
from jina.parsers import set_pod_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))
single_compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
shards_compose_yml = os.path.join(cur_dir, 'docker-compose-shards.yml')
exposed_port = 12345


@pytest.fixture
def external_pod_args():
    args = ['--port-in', str(45678)]
    args = vars(set_pod_parser().parse_args(args))
    del args['external']
    del args['pod_role']
    del args['host']
    return args


@pytest.fixture
def local_flow(external_pod_args):
    return Flow(port_expose=exposed_port).add(
        **external_pod_args, host='10.1.0.100', external=True
    )


@pytest.fixture
def documents_to_index():
    image = np.random.random((50, 50))
    return [Document(content=image) for i in range(200)]


@pytest.mark.parametrize(
    'docker_compose',
    [single_compose_yml, shards_compose_yml],
    indirect=['docker_compose'],
)
def test_local_flow_use_external_executor(
    local_flow, documents_to_index, docker_compose
):
    with local_flow as f:
        responses = Client(port=exposed_port).index(
            inputs=documents_to_index, return_results=True, request_size=100
        )
        assert len(responses) == 2
        for resp in responses:
            assert len(resp.docs) == 100
