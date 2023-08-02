import os

import pytest
from docarray import Document

from jina import Executor, Flow, requests


class MyExec(Executor):
    @requests
    def foo(self, docs, **kwargs):
        pass


@pytest.fixture
def cert_prefix():
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    return f'{cur_dir}/../../../unit/serve/runtimes/gateway/grpc/cert/'


@pytest.fixture
def cert_pem(cert_prefix):
    """This is the cert entry of a self-signed local cert"""
    return cert_prefix + '/server.crt'


@pytest.fixture
def key_pem(cert_prefix):
    """This is the key entry of a self-signed local cert"""
    return cert_prefix + '/server.key'


@pytest.mark.parametrize('protocol', ['http', 'websocket', 'grpc'])
@pytest.mark.parametrize('tls', [True, False])
@pytest.mark.parametrize(
    'uses',
    ['jinaai+sandbox://jina-ai/DummyHubExecutor'],
)
def test_deployment_protocol(protocol, tls, cert_pem, key_pem, uses):
    cert = cert_pem if tls else None
    key = key_pem if tls else None
    f = (
        Flow(protocol=protocol)
        .config_gateway(ssl_certfile=cert, ssl_keyfile=key)
        .add(uses=MyExec)
        .add(uses=uses)
    )
    with f:
        for node, v in f._deployment_nodes.items():
            p = v.protocol.lower()
            if node == 'gateway':
                assert p == protocol + ('s' if tls else '')
            elif node == 'executor0':
                assert p == 'grpc'
            elif node == 'executor1':
                assert p == 'grpcs'
