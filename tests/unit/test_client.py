import os
import time

import numpy as np
import requests
from jina.clients import py_client
from jina.clients.python import PyClient
from jina.clients.python.io import input_files, input_numpy
from jina.drivers.helper import array2pb
from jina.enums import ClientMode
from jina.flow import Flow
from jina.main.parser import set_gateway_parser
from jina.peapods.gateway import RESTGatewayPea
from jina.proto.jina_pb2 import Document
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


class ClientTestCase(JinaTestCase):

    def test_client(self):
        f = Flow().add(uses='_pass')
        with f:
            print(py_client(port_expose=f.port_expose).call_unary(b'a1234', mode=ClientMode.INDEX))

    def tearDown(self) -> None:
        super().tearDown()
        time.sleep(3)

    def test_check_input(self):
        input_fn = iter([b'1234', b'45467'])
        PyClient.check_input(input_fn)
        input_fn = iter([Document(), Document()])
        PyClient.check_input(input_fn)
        bad_input_fn = iter([b'1234', '45467', [12, 2, 3]])
        self.assertRaises(TypeError, PyClient.check_input, bad_input_fn)
        bad_input_fn = iter([Document(), None])
        self.assertRaises(TypeError, PyClient.check_input, bad_input_fn)

    def test_gateway_ready(self):
        p = set_gateway_parser().parse_args([])
        with RESTGatewayPea(p):
            a = requests.get(f'http://0.0.0.0:{p.port_expose}/ready')
            assert a.status_code == 200

        with RESTGatewayPea(p):
            a = requests.post(f'http://0.0.0.0:{p.port_expose}/api/ass')
            assert a.status_code == 405

    def test_gateway_index(self):
        f = Flow(rest_api=True).add(uses='_pass')
        with f:
            a = requests.post(f'http://0.0.0.0:{f.port_expose}/api/index',
                              json={'data': [
                                  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC',
                                  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC']})

            j = a.json()
            self.assertTrue('index' in j)
            assert len(j['index']['docs']) == 2
            assert j['index']['docs'][0]['uri'] == 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC'
            assert a.status_code == 200

    def test_gateway_index_with_args(self):
        f = Flow(rest_api=True).add(uses='_pass')
        with f:
            a = requests.post(f'http://0.0.0.0:{f.port_expose}/api/index',
                              json={'data': [
                                  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC',
                                  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC'],
                                  'first_doc_id': 0,
                              })
            j = a.json()
            self.assertTrue('index' in j)
            assert len(j['index']['docs']) == 2
            assert j['index']['docs'][0]['id'] == 1  # doc zero is reserved
            assert j['index']['docs'][1]['id'] == 2
            assert j['index']['docs'][0]['uri'] == 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC'
            assert a.status_code == 200

    def test_io_files(self):
        PyClient.check_input(input_files('*.*'))
        PyClient.check_input(input_files('*.*', recursive=True))
        PyClient.check_input(input_files('*.*', size=2))
        PyClient.check_input(input_files('*.*', size=2, read_mode='rb'))
        PyClient.check_input(input_files('*.*', sampling_rate=.5))

        f = Flow().add(uses='- !URI2Buffer {}')

        def validate_mime_type(req):
            for d in req.index.docs:
                assert d.mime_type == 'text/x-python'

        with f:
            f.index(input_files('*.py'), validate_mime_type)

    def test_io_np(self):
        print(type(np.random.random([100, 4])))
        PyClient.check_input(input_numpy(np.random.random([100, 4, 2])))
        PyClient.check_input(['asda', 'dsadas asdasd'])

        print(type(array2pb(np.random.random([100, 4, 2]))))
