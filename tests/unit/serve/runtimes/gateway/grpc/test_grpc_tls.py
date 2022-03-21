import os

import grpc
import pytest
from docarray import Document

from jina import Client, Flow
from jina.parsers import set_gateway_parser
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.types.request.control import ControlRequest


@pytest.fixture
def cert_pem():
    """This is the cert entry of a self-signed local cert"""
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    return f'{cur_dir}/cert/server.crt'


@pytest.fixture
def key_pem():
    """This is the key entry of a self-signed local cert"""
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    return f'{cur_dir}/cert/server.key'


def test_grpc_ssl(cert_pem, key_pem):
    args = set_gateway_parser().parse_args(
        [
            '--grpc-server-kwargs',
            f'ssl_certfile: {cert_pem}',
            f'ssl_keyfile: {key_pem}',
        ]
    )
    with GRPCGatewayRuntime(args):
        pass


def test_grpc_ssl_with_flow(cert_pem, key_pem):
    with Flow(
        protocol='grpc',
        grpc_server_kwargs=[
            f'ssl_certfile: {cert_pem}',
            f'ssl_keyfile: {key_pem}',
        ],
        tls=True,
    ) as f:
        os.environ['JINA_LOG_LEVEL'] = 'ERROR'

        with pytest.raises(grpc.aio._call.AioRpcError):
            Client(protocol='grpc', port=f.port, tls=True).index([Document()])


def test_grpc_ssl_with_flow_and_client(cert_pem, key_pem):
    port = 1234
    with Flow(
        protocol='grpc',
        grpc_server_kwargs=[
            f'ssl_certfile: {cert_pem}',
            f'ssl_keyfile: {key_pem}',
        ],
        port=port,
        tls=True,
    ):
        os.environ['JINA_LOG_LEVEL'] = 'ERROR'

        with open(cert_pem, 'rb') as f:
            creds = f.read()

        GrpcConnectionPool.send_request_sync(
            request=ControlRequest('STATUS'),
            target=f'localhost:{port}',
            root_certificates=creds,
            tls=True,
        )
