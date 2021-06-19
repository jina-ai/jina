import pytest

from jina import Flow
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
