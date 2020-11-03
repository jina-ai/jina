import uuid

from jina.logging import default_logger
from jina.parser import set_pea_parser
from jina.peapods.pea import BasePea
from jina.peapods.zmq import Zmqlet
from jina.proto import jina_pb2
from jina.proto.message import ProtoMessage


class MockBasePeaNotRead(BasePea):
    def post_hook(self, msg: 'ProtoMessage') -> 'BasePea':
        super().post_hook(msg)
        assert not msg.request.is_used


class MockBasePeaRead(BasePea):
    def post_hook(self, msg: 'ProtoMessage') -> 'BasePea':
        super().post_hook(msg)
        assert msg.request.is_used


args1 = set_pea_parser().parse_args([
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
    '--uses', '_clear',  # will trigger use
    '--timeout-ctrl', '-1'
])

args3 = set_pea_parser().parse_args([
    '--host-in', '0.0.0.0',
    '--host-out', '0.0.0.0',
    '--port-in', '12347',
    '--port-out', '12346',
    '--socket-in', 'PULL_BIND',
    '--socket-out', 'PUSH_BIND',
    '--uses', '_pass',  # will NOT trigger use
    '--timeout-ctrl', '-1'
])


def test_read_zmqlet():
    with MockBasePeaRead(args2), Zmqlet(args1, default_logger) as z:
        req = jina_pb2.Request()
        req.request_id = uuid.uuid1().hex
        d = req.index.docs.add()
        d.tags['id'] = 2
        msg = ProtoMessage(None, req, 'tmp', '')
        z.send_message(msg)


def test_not_read_zmqlet():
    with MockBasePeaNotRead(args3), Zmqlet(args1, default_logger) as z:
        req = jina_pb2.Request()
        req.request_id = uuid.uuid1().hex
        d = req.index.docs.add()
        d.tags['id'] = 2
        msg = ProtoMessage(None, req, 'tmp', '')
        z.send_message(msg)
