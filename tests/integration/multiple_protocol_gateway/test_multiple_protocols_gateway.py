import os
import time

import pytest
import requests
from docarray import Document

from jina import Client, Flow
from jina.helper import random_port
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from tests.integration.multiple_protocol_gateway.gateway.multiprotocol_gateway import (
    MultiProtocolGateway,
)

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='module')
def multi_port_gateway_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(
        path=os.path.join(cur_dir, 'gateway/'), tag='multiprotocol-gateway'
    )
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.mark.parametrize(
    'uses',
    [
        'MultiProtocolGateway',
        'docker://multiprotocol-gateway',
    ],
)
@pytest.mark.parametrize('use_stream', [False, True])
def test_multiple_protocols_gateway(multi_port_gateway_docker_image_built, uses, use_stream):
    http_port = random_port()
    grpc_port = random_port()
    flow = Flow().config_gateway(
        uses=uses, port=[http_port, grpc_port], protocol=['http', 'grpc']
    )
    assert flow.port == [http_port, grpc_port]
    grpc_client = Client(protocol='grpc', port=grpc_port)
    with flow:
        grpc_client.post('/', inputs=Document(), stream=use_stream)
        resp = requests.get(f'http://localhost:{http_port}').json()
        assert resp['protocol'] == 'http'
        assert AsyncNewLoopRuntime.is_ready(f'localhost:{grpc_port}')
