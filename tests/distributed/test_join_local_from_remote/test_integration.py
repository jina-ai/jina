import os

import pytest

from jina import Document, __default_host__
from jina.clients import Client
from jina.clients.grpc import GRPCClient
from jina.parsers import set_client_cli_parser
from tests import validate_callback
from ..helpers import create_workspace, wait_for_workspace, create_flow, assert_request

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yaml = os.path.join(cur_dir, 'flow.yml')
pod_dir = os.path.join(cur_dir, 'pods')


JINAD_HOST = __default_host__
GATEWAY_HOST = __default_host__
JINAD_PORT = 8000
GATEWAY_PORT = 45678


@pytest.fixture
def doc_to_index():
    doc = Document()
    doc.text = 'test'
    return doc


@pytest.fixture
def client():
    return Client(host='localhost', port=45678)


@pytest.fixture
def grpc_client():
    args = set_client_cli_parser().parse_args(
        ['--host', 'localhost', '--port', '45678']
    )

    return GRPCClient(args)


@pytest.fixture(params=['client', 'grpc_client'])
def client_instance(request):
    return request.getfixturevalue(request.param)


@pytest.mark.skip('jinad with docker-compose not supported for now')
@pytest.mark.timeout(360)
@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_flow(docker_compose, doc_to_index, client_instance, mocker):
    def validate_resp(resp):
        assert len(resp.data.docs) == 2
        assert resp.data.docs[0].text == 'test'
        assert resp.data.docs[1].text == 'test'

    mock = mocker.Mock()
    workspace_id = create_workspace(filepaths=[flow_yaml], dirpath=pod_dir)
    assert wait_for_workspace(workspace_id)
    flow_id = create_flow(
        workspace_id=workspace_id,
        filename='flow.yml',
    )

    client_instance.search(inputs=[doc_to_index], on_done=mock)

    assert_request(method='get', url=f'http://{JINAD_HOST}:8000/flows/{flow_id}')

    assert_request(
        method='delete',
        url=f'http://{JINAD_HOST}:8000/flows/{flow_id}',
        # payload={'workspace': False},
    )

    mock.assert_called_once()
    validate_callback(mock, validate_resp)
