import os
import time

import pytest
from docarray import Document

from jina import Client, Flow
from jina.serve.networking.utils import send_health_check_sync


@pytest.fixture
def error_log_level():
    old_env = os.environ.get('JINA_LOG_LEVEL')
    os.environ['JINA_LOG_LEVEL'] = 'ERROR'
    yield
    os.environ['JINA_LOG_LEVEL'] = old_env


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


def test_grpc_ssl_with_flow(cert_pem, key_pem, error_log_level):
    with Flow(
        protocol='grpc',
        ssl_certfile=cert_pem,
        ssl_keyfile=key_pem,
    ) as f:

        with pytest.raises(ConnectionError):
            Client(protocol='grpc', port=f.port, tls=True).index([Document()])
    # the openssl error from above seems to take a bit to actually terminate and may cause the next test to seg fault
    time.sleep(15.0)


def test_grpc_ssl_with_flow_and_client(cert_pem, key_pem, error_log_level):
    with Flow(
        protocol='grpc',
        ssl_certfile=cert_pem,
        ssl_keyfile=key_pem,
    ) as flow:
        with open(cert_pem, 'rb') as f:
            creds = f.read()

        send_health_check_sync(
            target=f'localhost:{flow.port}',
            root_certificates=creds,
            tls=True,
            timeout=1.0,
        )
    time.sleep(15.0)
