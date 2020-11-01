import pytest
import requests

from jina.clients import py_client
from jina.clients.python import PyClient
from jina.clients.python.io import input_files
from jina.enums import ClientMode
from jina.flow import Flow
from jina.helper import random_port
from jina.parser import set_gateway_parser
from jina.peapods.gateway import RESTGatewayPea
from jina.proto.jina_pb2 import Document


@pytest.fixture(scope='function')
def flow():
    return Flow(rest_api=False).add(uses='_pass')


@pytest.fixture(scope='function')
def flow_with_rest_api_enabled():
    return Flow(rest_api=True).add(uses='_pass')


@pytest.fixture(scope='function')
def test_img_1():
    return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC'


@pytest.fixture(scope='function')
def test_img_2():
    return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC'


def test_client(flow):
    with flow:
        py_client(port_expose=flow.port_expose).call_unary(
            b'a1234', mode=ClientMode.INDEX
        )


@pytest.mark.parametrize('input_fn', [iter([b'1234', b'45467']), iter([Document(), Document()])])
def test_check_input_success(input_fn):
    PyClient.check_input(input_fn)


@pytest.mark.parametrize('input_fn', [iter([b'1234', '45467', [12, 2, 3]]), iter([Document(), None])])
def test_check_input_fail(input_fn):
    with pytest.raises(TypeError):
        PyClient.check_input(input_fn)


@pytest.mark.parametrize(
    'port_expose, route, status_code',
    [
        (random_port(), '/ready', 200),
        (random_port(), '/api/ass', 405)
    ]
)
def test_gateway_ready(port_expose, route, status_code):
    p = set_gateway_parser().parse_args(['--port-expose', str(port_expose)])
    with RESTGatewayPea(p):
        a = requests.get(f'http://0.0.0.0:{p.port_expose}{route}')
        assert a.status_code == status_code


def test_gateway_index(flow_with_rest_api_enabled, test_img_1, test_img_2):
    with flow_with_rest_api_enabled:
        r = requests.post(
            f'http://0.0.0.0:{flow_with_rest_api_enabled.port_expose}/api/index',
            json={
                'data': [test_img_1, test_img_2]
            },
        )
        assert r.status_code == 200
        resp = r.json()
        assert 'index' in resp
        assert len(resp['index']['docs']) == 2
        assert resp['index']['docs'][0]['uri'] == test_img_1


def test_mime_type():
    f = Flow().add(uses='- !URI2Buffer {}')

    def validate_mime_type(req):
        for d in req.index.docs:
            assert d.mime_type == 'text/x-python'

    with f:
        f.index(input_files('*.py'), validate_mime_type)
