from jina.clients import py_client
from jina.clients.python import PyClient
from jina.flow import Flow
from jina.proto.jina_pb2 import Document
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_client(self):
        f = Flow().add(yaml_path='_forward')
        with f:
            print(py_client(port_grpc=f.port_grpc).call_unary(b'a1234', mode='index'))

    def test_check_input(self):
        input_fn = iter([b'1234', b'45467'])
        PyClient.check_input(input_fn)
        input_fn = iter([Document(), Document()])
        PyClient.check_input(input_fn, in_proto=True)
        bad_input_fn = iter([b'1234', '45467'])
        self.assertRaises(TypeError, PyClient.check_input, bad_input_fn)
        bad_input_fn = iter([Document()])
        self.assertRaises(TypeError, PyClient.check_input, bad_input_fn)
