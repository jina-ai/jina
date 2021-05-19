import pytest

from jina import Flow
from tests import random_docs


@pytest.mark.parametrize('restful', [True, False])
@pytest.mark.parametrize('changeto_gateway', ['GRPCGateway', 'RESTGateway'])
def test_change_gateway(restful, changeto_gateway, mocker):
    f = Flow(restful=restful).add().add().add(needs='pod1').needs_all()

    with f:
        mock = mocker.Mock()
        f.post('', random_docs(10), on_done=mock)
        mock.assert_called()

        mock = mocker.Mock()
        if changeto_gateway == 'RESTGateway':
            f.use_rest_gateway()
        if changeto_gateway == 'GRPCGateway':
            f.use_grpc_gateway()

        f.post('', random_docs(10), on_done=mock)
        mock.assert_called()
