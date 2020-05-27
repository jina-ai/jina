import time

import requests

from jina.clients import py_client
from jina.clients.python import PyClient
from jina.enums import ClientInputType, ClientMode
from jina.flow import Flow
from jina.main.parser import set_gateway_parser
from jina.peapods.gateway import RESTGatewayPea
from jina.proto.jina_pb2 import Document
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_client(self):
        f = Flow().add(yaml_path='_forward')
        with f:
            print(py_client(port_grpc=f.port_grpc).call_unary(b'a1234', mode=ClientMode.INDEX))

    def tearDown(self) -> None:
        super().tearDown()
        time.sleep(3)

    def test_check_input(self):
        input_fn = iter([b'1234', b'45467'])
        PyClient.check_input(input_fn)
        input_fn = iter([Document(), Document()])
        PyClient.check_input(input_fn, input_type=ClientInputType.PROTOBUF)
        bad_input_fn = iter([b'1234', '45467', [12, 2, 3]])
        self.assertRaises(TypeError, PyClient.check_input, bad_input_fn)
        bad_input_fn = iter([Document(), None])
        self.assertRaises(TypeError, PyClient.check_input, bad_input_fn)

    def test_gateway_ready(self):
        p = set_gateway_parser().parse_args([])
        with RESTGatewayPea(p):
            a = requests.get(f'http://0.0.0.0:{p.port_grpc}/ready')
            self.assertEqual(a.status_code, 200)

        with RESTGatewayPea(p):
            a = requests.post(f'http://0.0.0.0:{p.port_grpc}/api/ass')
            self.assertEqual(a.status_code, 405)

    def test_gateway_index(self):
        f = Flow(rest_api=True).add(yaml_path='_forward')
        with f:
            a = requests.post(f'http://0.0.0.0:{f.port_grpc}/api/index',
                              json={'data': [
                                  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC',
                                  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC']})

            j = a.json()
            self.assertTrue('index' in j)
            self.assertEqual(len(j['index']['docs']), 2)
            self.assertEqual(j['index']['docs'][0]['dataUri'],
                             'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC')
            self.assertEqual(a.status_code, 200)

    def test_gateway_index_with_args(self):
        f = Flow(rest_api=True).add(yaml_path='_forward')
        with f:
            a = requests.post(f'http://0.0.0.0:{f.port_grpc}/api/index',
                              json={'data': [
                                  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC',
                                  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC'],
                                  'first_doc_id': 5,
                              })
            j = a.json()
            self.assertTrue('index' in j)
            self.assertEqual(len(j['index']['docs']), 2)
            self.assertEqual(j['index']['docs'][0]['docId'], 5)
            self.assertEqual(j['index']['docs'][1]['docId'], 6)
            self.assertEqual(j['index']['docs'][0]['dataUri'],
                             'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC')
            self.assertEqual(a.status_code, 200)
