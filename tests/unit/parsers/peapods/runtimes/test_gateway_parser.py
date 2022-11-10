import pytest

from jina.enums import GatewayProtocolType
from jina.helper import ArgNamespace
from jina.parsers import set_gateway_parser

# TODO: make sure this file is covered in CI


@pytest.mark.parametrize(
    'port,expected_port',
    [
        ('12345', ['12345']),
        ([12345], ['12345']),
        ([12345, 12344], ['12345', '12344']),
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
        (['12345'], ['12345']),
        (['12345', '12344'], ['12345', '12344']),
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
