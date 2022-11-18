import os
import time

import pytest
import requests
from docarray import Document

from jina import Client, Flow
from jina.helper import random_port
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime

from .gateway.multiprotocol_gateway import MultiProtocolGateway

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='module')
def multi_port_gateway_docker_image_built():
    import docker

    client = docker.from_env()
    print('building container image')
    client.images.build(
        path=os.path.join(cur_dir, 'gateway/'), tag='multiprotcol-gateway'
    )
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.mark.parametrize(
    'uses',
    [
        # sigterm not being handled properly in http server
        # 'MultiProtocolGateway',
        'docker://multiprotcol-gateway',
    ],
)
def test_multiple_protocols_gateway(multi_port_gateway_docker_image_built, uses):
    http_port = random_port()
    grpc_port = random_port()
    flow = Flow().config_gateway(
        uses=uses, port=[http_port, grpc_port], protocol=['http', 'grpc']
    )
    assert flow.port == [http_port, grpc_port]
    grpc_client = Client(protocol='grpc', port=grpc_port)
    with flow:
        grpc_client.post('/', inputs=Document())
        resp = requests.get(f'http://localhost:{http_port}').json()
        assert resp['protocol'] == 'http'
        assert AsyncNewLoopRuntime.is_ready(f'localhost:{grpc_port}')


def test_multiple_protocol_disallowed_for_builtin_gateways():
    flow = Flow().config_gateway(protocol=['http', 'grpc'])
    with pytest.raises(ValueError) as error_info:
        with flow:
            pass
    assert (
        'You need to specify exactly 1 protocol if you want to use a jina built-in gateway'
        in str(error_info.value)
    )
