import os

import pytest

from jina import Document
from jina.clients import Client
from jina.clients.grpc import GRPCClient
from jina.parsers import set_client_cli_parser
from tests import validate_callback
from ..helpers import create_flow, assert_request

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yaml = os.path.join(cur_dir, 'flow.yml')
pod_dir = os.path.join(cur_dir, 'pods')


@pytest.fixture
def doc_to_index():
    doc = Document()
    doc.text = 'test'
    return doc


@pytest.fixture
def client():
    return Client(host='localhost', port_expose=45678)


@pytest.fixture
def grpc_client():
    args = set_client_cli_parser().parse_args(
        ['--host', 'localhost', '--port-expose', '45678']
    )

    return GRPCClient(args)


@pytest.fixture(params=['client', 'grpc_client'])
def client_instance(request):
    return request.getfixturevalue(request.param)


@pytest.mark.timeout(360)
@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_flow(docker_compose, doc_to_index, client_instance, mocker):
    def validate_resp(resp):
        assert len(resp.data.docs) == 2
        assert resp.data.docs[0].text == 'test'
        assert resp.data.docs[1].text == 'test'

    mock = mocker.Mock()
    flow_id = create_flow(flow_yaml=flow_yaml, pod_dir=os.path.join(cur_dir, 'pods'))

    client_instance.search(inputs=[doc_to_index], on_done=mock)

    assert_request(method='get', url=f'http://localhost:8000/flows/{flow_id}')

    assert_request(
        method='delete',
        url=f'http://localhost:8000/flows/{flow_id}',
        payload={'workspace': False},
    )

    mock.assert_called_once()
    validate_callback(mock, validate_resp)
