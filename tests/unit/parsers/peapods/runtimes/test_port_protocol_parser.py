import pytest

from jina.enums import GatewayProtocolType
from jina.helper import ArgNamespace
from jina.parsers import set_gateway_parser, set_pod_parser


@pytest.mark.parametrize(
    'port,expected_port',
    [
        ('12345', [12345]),
        ([12345], [12345]),
        ([12345, 12344], [12345, 12344]),
    ],
)
@pytest.mark.parametrize(
    'protocol,expected_protocol',
    [
        ('http', [GatewayProtocolType.HTTP]),
        (['GRPC'], [GatewayProtocolType.GRPC]),
        (['grpc', 'http'], [GatewayProtocolType.GRPC, GatewayProtocolType.HTTP]),
    ],
)
def test_multiple_port_protocol_gateway_kwargs(
    port, protocol, expected_port, expected_protocol
):
    args = ArgNamespace.kwargs2namespace(
        {'port': port, 'protocol': protocol}, set_gateway_parser()
    )
    assert args.port == expected_port
    assert args.protocol == expected_protocol


@pytest.mark.parametrize(
    'port,expected_port',
    [
        (['12345'], [12345]),
        (['12345', '12344'], [12345, 12344]),
        (['12345, 12344'], [12345, 12344]),
    ],
)
@pytest.mark.parametrize(
    'protocol,expected_protocol',
    [
        (['http'], [GatewayProtocolType.HTTP]),
        (['GRPC'], [GatewayProtocolType.GRPC]),
        (['grpc', 'http'], [GatewayProtocolType.GRPC, GatewayProtocolType.HTTP]),
    ],
)
def test_multiple_port_protocol_gateway_args_list(
    port, protocol, expected_port, expected_protocol
):
    args = set_gateway_parser().parse_args(
        ['--port'] + port + ['--protocol'] + protocol
    )
    assert args.port == expected_port
    assert args.protocol == expected_protocol


@pytest.mark.parametrize(
    'port,expected_port',
    [
        (['12345'], [12345]),
        (['12345', '12344'], [12345, 12344]),
        (['12345, 12344'], [12345, 12344]),
    ],
)
def test_pod_port_cast(port, expected_port):
    args = set_pod_parser().parse_args(['--port'] + port)
    assert args.port == expected_port


def test_pod_port_default():
    args = set_pod_parser().parse_args([])
    assert isinstance(args.port, list)
    assert len(args.port) == 1


@pytest.mark.parametrize(
    'host,expected_host',
    [
        (['localhost'], ['localhost']),
        (['0.0.0.0,localhost'], ['0.0.0.0', 'localhost']),
        (['0.0.0.0,localhost', '127.0.0.1'], ['0.0.0.0', 'localhost', '127.0.0.1']),
    ],
)
def test_pod_host_cast(host, expected_host):
    args = set_pod_parser().parse_args(['--host'] + host)
    assert args.host == expected_host


def test_pod_host_default():
    from jina.constants import __default_host__

    args = set_pod_parser().parse_args([])
    assert args.host == [__default_host__]


def test_default_port_protocol_gateway():
    args = set_gateway_parser().parse_args([])
    assert len(args.port) == 1
    assert args.protocol == [GatewayProtocolType.GRPC]


def test_get_non_defaults_args():
    args = set_gateway_parser().parse_args(
        [
            '--port',
            '12345',
            '12344',
            '--protocol',
            'grpc',
            '--uses',
            'MyCustomGateway',
            '--uses-with',
            '{"arg":"value"}',
        ]
    )
    non_defaults = ArgNamespace.get_non_defaults_args(
        args,
        set_gateway_parser(),
    )
    assert non_defaults['port'] == [12345, 12344]
    assert 'protocol' not in non_defaults
    assert non_defaults['uses'] == 'MyCustomGateway'
    assert non_defaults['uses_with'] == {'arg': 'value'}
