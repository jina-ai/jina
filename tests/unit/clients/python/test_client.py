import os
import time

import pytest
import requests

from jina import Executor, DocumentArray, requests as req
from jina import Flow
from jina import helper, Document
from jina.clients import Client
from jina.excepts import BadClientInput
from jina.parsers import set_gateway_parser
from jina.peapods import Pea
from jina.proto.jina_pb2 import DocumentProto
from jina.types.document.generators import from_csv, from_ndjson, from_files
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def flow():
    return Flow(protocol='grpc').add()


@pytest.fixture(scope='function')
def flow_with_websocket():
    return Flow(protocol='websocket').add()


@pytest.fixture(scope='function')
def flow_with_http():
    return Flow(protocol='http').add()


@pytest.fixture(scope='function')
def test_img_1():
    return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC'


@pytest.fixture(scope='function')
def test_img_2():
    return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC'


@pytest.mark.parametrize(
    'inputs', [iter([b'1234', b'45467']), iter([DocumentProto(), DocumentProto()])]
)
def test_check_input_success(inputs):
    client = Client(host='localhost', port_expose=12345)
    client.check_input(inputs)


@pytest.mark.parametrize(
    'inputs', [iter([list(), list(), [12, 2, 3]]), iter([set(), set()])]
)
def test_check_input_fail(inputs):
    client = Client(host='localhost', port_expose=12345)
    with pytest.raises(BadClientInput):
        client.check_input(inputs)


@pytest.mark.parametrize(
    'port_expose, route, status_code',
    [(helper.random_port(), '/status', 200), (helper.random_port(), '/api/ass', 404)],
)
def test_gateway_ready(port_expose, route, status_code):
    p = set_gateway_parser().parse_args(
        ['--port-expose', str(port_expose), '--protocol', 'http']
    )
    with Pea(p):
        time.sleep(0.5)
        a = requests.get(f'http://localhost:{p.port_expose}{route}')
        assert a.status_code == status_code


def test_gateway_index(flow_with_http, test_img_1, test_img_2):
    with flow_with_http:
        time.sleep(0.5)
        r = requests.post(
            f'http://localhost:{flow_with_http.port_expose}/index',
            json={'data': [test_img_1, test_img_2]},
        )
        assert r.status_code == 200
        resp = r.json()
        assert 'data' in resp
        assert len(resp['data']['docs']) == 2
        assert resp['data']['docs'][0]['uri'] == test_img_1


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_mime_type(protocol):
    class MyExec(Executor):
        @req
        def foo(self, docs: 'DocumentArray', **kwargs):
            for d in docs:
                d.convert_uri_to_buffer()

    f = Flow(protocol=protocol).add(uses=MyExec)

    def validate_mime_type(req):
        for d in req.data.docs:
            assert d.mime_type == 'text/x-python'

    with f:
        f.index(from_files('*.py'), validate_mime_type)


@pytest.mark.parametrize('func_name', ['index', 'search'])
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_client_ndjson(protocol, mocker, func_name):
    with Flow(protocol=protocol).add() as f, open(
        os.path.join(cur_dir, 'docs.jsonlines')
    ) as fp:
        mock = mocker.Mock()
        getattr(f, f'{func_name}')(from_ndjson(fp), on_done=mock)
        mock.assert_called_once()


@pytest.mark.parametrize('func_name', ['index', 'search'])
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_client_csv(protocol, mocker, func_name):
    with Flow(protocol=protocol).add() as f, open(
        os.path.join(cur_dir, 'docs.csv')
    ) as fp:
        mock = mocker.Mock()
        getattr(f, f'{func_name}')(from_csv(fp), on_done=mock)
        mock.assert_called_once()


# Timeout is necessary to fail in case of hanging client requests
@pytest.mark.timeout(5)
def test_client_websocket(mocker, flow_with_websocket):
    with flow_with_websocket:
        time.sleep(0.5)
        client = Client(
            host='localhost',
            port_expose=str(flow_with_websocket.port_expose),
            protocol='websocket',
        )
        # Test that a regular index request triggers the correct callbacks
        on_always_mock = mocker.Mock()
        on_error_mock = mocker.Mock()
        on_done_mock = mocker.Mock()
        client.post(
            '',
            random_docs(1),
            request_size=1,
            on_always=on_always_mock,
            on_error=on_error_mock,
            on_done=on_done_mock,
        )
        on_always_mock.assert_called_once()
        on_done_mock.assert_called_once()
        on_error_mock.assert_not_called()


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_client_from_kwargs(protocol):
    Client(port_expose=12345, host='0.0.0.1', protocol=protocol)


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_independent_client(protocol):
    with Flow(protocol=protocol) as f:
        c = Client(host='localhost', port_expose=f.port_expose, protocol=protocol)
        assert type(c) == type(f.client)
        c.post('/')


@pytest.mark.parametrize('protocol', ['http', 'grpc', 'websocket'])
def test_all_sync_clients(protocol, mocker):
    from jina import requests

    class MyExec(Executor):
        @requests
        def foo(self, docs, **kwargs):
            pass

    f = Flow(protocol=protocol).add(uses=MyExec)
    docs = list(random_docs(1000))
    m1 = mocker.Mock()
    m2 = mocker.Mock()
    m3 = mocker.Mock()
    m4 = mocker.Mock()
    with f:
        f.post('', on_done=m1)
        f.post('/foo', docs, on_done=m2)
        f.post('/foo', on_done=m3)
        f.post('/foo', docs, parameters={'hello': 'world'}, on_done=m4)

    m1.assert_called_once()
    m2.assert_called()
    m3.assert_called_once()
    m4.assert_called()
