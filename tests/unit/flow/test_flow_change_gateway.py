import pytest

from jina import Flow
from jina.enums import GatewayProtocolType
from tests import random_docs


@pytest.mark.parametrize('protocol', ['http', 'websocket', 'grpc'])
@pytest.mark.parametrize('changeto_protocol', ['grpc', 'http', 'websocket'])
def test_change_gateway(protocol, changeto_protocol, mocker):
    f = Flow(protocol=protocol).add().add().add(needs='pod1').needs_all()

    with f:
        mock = mocker.Mock()
        f.post('', random_docs(10), on_done=mock)
        mock.assert_called()

        mock = mocker.Mock()
        f.protocol = changeto_protocol

        f.post('', random_docs(10), on_done=mock)
        mock.assert_called()


@pytest.mark.parametrize('protocol', ['http', 'websocket', 'grpc'])
def test_get_set_client_gateway_in_flow(protocol):
    f = Flow(protocol=protocol, port_expose=12345)
    assert f.client_args.protocol == GatewayProtocolType.from_string(protocol)
    assert f.gateway_args.protocol == GatewayProtocolType.from_string(protocol)
    assert f.client_args.port_expose == 12345
    assert f.gateway_args.port_expose == 12345
    f.update_network_interface(port_expose=54321)
    assert f.client_args.port_expose == 54321
