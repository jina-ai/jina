from jina.flow import Flow
from jina.main.parser import set_pea_parser
from jina.peapods.pea import BasePea
from jina.peapods.zmq import Zmqlet, add_envelope
from jina.proto import jina_pb2
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_simple_zmqlet(self):
        args = set_pea_parser().parse_args([
            '--host-in', '0.0.0.0',
            '--host-out', '0.0.0.0',
            '--port-in', '12346',
            '--port-out', '12347',
            '--socket-in', 'PULL_CONNECT',
            '--socket-out', 'PUSH_CONNECT',
            '--timeout-ctrl', '-1'])

        args2 = set_pea_parser().parse_args([
            '--host-in', '0.0.0.0',
            '--host-out', '0.0.0.0',
            '--port-in', '12347',
            '--port-out', '12346',
            '--socket-in', 'PULL_BIND',
            '--socket-out', 'PUSH_BIND',
            '--yaml-path', '_logforward',
            '--timeout-ctrl', '-1'
        ])

        with BasePea(args2) as z1, Zmqlet(args) as z:
            req = jina_pb2.Request()
            req.request_id = 1
            d = req.index.docs.add()
            d.doc_id = 2
            msg = add_envelope(req, 'tmp', '')
            z.send_message(msg)

    def test_flow_with_jump(self):
        f = (Flow().add(name='r1', yaml_path='_forward')
             .add(name='r2', yaml_path='_forward')
             .add(name='r3', yaml_path='_forward', needs='r1')
             .add(name='r4', yaml_path='_forward', needs='r2')
             .add(name='r5', yaml_path='_forward', needs='r3')
             .add(name='r6', yaml_path='_forward', needs='r4')
             .add(name='r8', yaml_path='_forward', needs='r6')
             .add(name='r9', yaml_path='_forward', needs='r5')
             .add(name='r10', yaml_path='_merge', needs=['r9', 'r8']))

        with f:
            f.dry_run()
