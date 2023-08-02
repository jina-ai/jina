import pytest

from jina import Client
from jina.enums import ProtocolType


@pytest.mark.parametrize(
    'protocol, gateway_type',
    [
        ('http', ProtocolType.HTTP),
        ('grpc', ProtocolType.GRPC),
        ('ws', ProtocolType.WEBSOCKET),
        (None, None),
    ],
)
@pytest.mark.parametrize('tls', [True, False])
@pytest.mark.parametrize('hostname', ['localhost', 'executor.jina.ai'])
def test_host_unpacking(protocol, gateway_type, tls, hostname):
    port = 1234

    protocol = f'{protocol}s' if tls and protocol else protocol

    scheme = f'{protocol}://' if protocol else ''

    host = f'{scheme}{hostname}:{port}'

    c = Client(host=host) if scheme else Client(host=host, tls=tls)

    if gateway_type:
        assert c.args.protocol == gateway_type

    assert c.args.host == hostname
    assert c.args.port == port
    assert c.args.tls == tls


@pytest.mark.parametrize('protocol', ['https', 'grpcs', 'wss'])
@pytest.mark.parametrize('port', [1234, None])
def test_host_unpacking_port_tls(protocol, port):
    port_scheme = f':{port}' if port else ''

    host = f'{protocol}://localhost{port_scheme}'

    c = Client(host=host)

    assert c.args.port == port if port else 443


@pytest.mark.parametrize('protocol', ['http', 'grpc', 'ws'])
@pytest.mark.parametrize('port', [1234, None])
def test_host_unpacking_port(protocol, port):
    port_scheme = f':{port}' if port else ''

    host = f'{protocol}://localhost{port_scheme}'

    c = Client(host=host)

    assert c.args.port == port if port else 80


def test_delete_slash_host():
    host = f'http://localhost/'

    c = Client(host=host)

    assert c.args.host == 'localhost'


def test_host_unpacking_basic():
    protocol = 'http'
    hostname = 'localhost'

    host = f'{protocol}://{hostname}'
    c = Client(host=host)

    assert c.args.protocol == ProtocolType.HTTP
    assert c.args.host == hostname


def test_host_unpacking_duplicate():
    with pytest.raises(ValueError):
        Client(host=f'http://localhost:1234', port=1234)


def test_log_config_arg():
    cli_args = ['--log-config', 'logging.custom.yml']

    from jina.parsers import set_client_cli_parser

    args = set_client_cli_parser().parse_args(cli_args)
    assert args.log_config == 'logging.custom.yml'
