import pytest

from jina import Client
from jina.enums import GatewayProtocolType


@pytest.mark.parametrize(
    'protocol, gateway_type',
    [
        ('http', GatewayProtocolType.HTTP),
        ('grpc', GatewayProtocolType.GRPC),
        ('ws', GatewayProtocolType.WEBSOCKET),
    ],
)
@pytest.mark.parametrize('tls', [True, False])
@pytest.mark.parametrize('hostname', ['localhost', 'executor.jina.ai'])
def test_host_unpacking(protocol, gateway_type, tls, hostname):

    port = 1234

    _s = 's' if tls else ''
    host = f'{protocol}{_s}://{hostname}:{port}'
    c = Client(host=host)

    assert c.args.protocol == gateway_type
    assert c.args.host == hostname
    assert c.args.port == port
    assert c.args.https == tls


def test_host_unpacking_port():

    protocol = 'http'
    hostname = 'localhost'

    host = f'{protocol}://{hostname}'
    c = Client(host=host)

    assert c.args.protocol == GatewayProtocolType.HTTP
    assert c.args.host == hostname
