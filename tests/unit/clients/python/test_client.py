import os
import time

import pytest
import requests

from jina.clients import Client
from jina.clients.sugary_io import _input_files
from jina.excepts import BadClientInput
from jina.flow import Flow
from jina import helper
from jina.parsers import set_gateway_parser
from jina.peapods import Pea
from jina.proto.jina_pb2 import DocumentProto

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def flow():
    return Flow(rest_api=False).add()


@pytest.fixture(scope='function')
def flow_with_rest_api_enabled():
    return Flow(rest_api=True).add()


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
    Client.check_input(inputs)


@pytest.mark.parametrize(
    'inputs', [iter([list(), list(), [12, 2, 3]]), iter([set(), set()])]
)
def test_check_input_fail(inputs):
    with pytest.raises(BadClientInput):
        Client.check_input(inputs)


@pytest.mark.parametrize(
    'port_expose, route, status_code',
    [(helper.random_port(), '/status', 200), (helper.random_port(), '/api/ass', 405)],
)
def test_gateway_ready(port_expose, route, status_code):
    p = set_gateway_parser().parse_args(
        ['--port-expose', str(port_expose), '--runtime-cls', 'RESTRuntime']
    )
    with Pea(p):
        time.sleep(0.5)
        a = requests.get(f'http://0.0.0.0:{p.port_expose}{route}')
        assert a.status_code == status_code


def test_gateway_index(flow_with_rest_api_enabled, test_img_1, test_img_2):
    with flow_with_rest_api_enabled:
        time.sleep(0.5)
        r = requests.post(
            f'http://0.0.0.0:{flow_with_rest_api_enabled.port_expose}/api/index',
            json={'data': [test_img_1, test_img_2]},
        )
        assert r.status_code == 200
        resp = r.json()
        assert 'index' in resp
        assert len(resp['index']['docs']) == 2
        assert resp['index']['docs'][0]['uri'] == test_img_1


@pytest.mark.parametrize('restful', [False, True])
def test_mime_type(restful):
    f = Flow(restful=restful).add(uses='- !URI2Buffer {}')

    def validate_mime_type(req):
        for d in req.index.docs:
            assert d.mime_type == 'text/x-python'

    with f:
        f.index(_input_files('*.py'), validate_mime_type)


@pytest.mark.parametrize('func_name', ['index', 'search'])
@pytest.mark.parametrize('restful', [False, True])
def test_client_ndjson(restful, mocker, func_name):
    with Flow(restful=restful).add() as f, open(
        os.path.join(cur_dir, 'docs.jsonlines')
    ) as fp:
        mock = mocker.Mock()
        getattr(f, f'{func_name}_ndjson')(fp, on_done=mock)
        mock.assert_called_once()


@pytest.mark.parametrize('func_name', ['index', 'search'])
@pytest.mark.parametrize('restful', [False, True])
def test_client_csv(restful, mocker, func_name):
    with Flow(restful=restful).add() as f, open(
        os.path.join(cur_dir, 'docs.csv')
    ) as fp:
        mock = mocker.Mock()
        getattr(f, f'{func_name}_csv')(fp, on_done=mock)
        mock.assert_called_once()
