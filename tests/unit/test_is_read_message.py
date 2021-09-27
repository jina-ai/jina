import time

from jina import __default_executor__
from jina.helper import random_identity
from jina.logging.predefined import default_logger
from jina.parsers import set_pea_parser
from jina.peapods.peas import BasePea
from jina.peapods.zmq import Zmqlet
from jina.types.message import Message
from jina.types.request import Request
from tests import validate_callback


class MockBasePeaNotRead(BasePea):
    def _post_hook(self, msg: 'Message') -> 'BasePea':
        super()._post_hook(msg)
        assert not msg.request.is_decompressed


class MockBasePeaRead(BasePea):
    def _post_hook(self, msg: 'Message') -> 'BasePea':
        super()._post_hook(msg)
        assert msg.request.is_decompressed


args1 = set_pea_parser().parse_args(
    [
        '--host-in',
        '0.0.0.0',
        '--host-out',
        '0.0.0.0',
        '--socket-in',
        'PULL_CONNECT',
        '--socket-out',
        'PUSH_CONNECT',
        '--timeout-ctrl',
        '-1',
    ]
)

args2 = set_pea_parser().parse_args(
    [
        '--host-in',
        '0.0.0.0',
        '--host-out',
        '0.0.0.0',
        '--port-in',
        str(args1.port_out),
        '--port-out',
        str(args1.port_in),
        '--socket-in',
        'PULL_BIND',
        '--socket-out',
        'PUSH_BIND',
        '--timeout-ctrl',
        '-1',
    ]
)

args3 = set_pea_parser().parse_args(
    [
        '--host-in',
        '0.0.0.0',
        '--host-out',
        '0.0.0.0',
        '--port-in',
        str(args1.port_out),
        '--port-out',
        str(args1.port_in),
        '--socket-in',
        'PULL_BIND',
        '--socket-out',
        'PUSH_BIND',
        '--uses',
        __default_executor__,  # will NOT trigger use
        '--timeout-ctrl',
        '-1',
    ]
)


def test_read_zmqlet():
    with MockBasePeaRead(args2), Zmqlet(args1, default_logger) as z:
        req = Request()
        req.request_id = random_identity()
        d = req.data.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')
        z.send_message(msg)


def test_not_read_zmqlet():
    with MockBasePeaNotRead(args3), Zmqlet(args1, default_logger) as z:
        req = Request()
        req.request_id = random_identity()
        d = req.data.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')
        z.send_message(msg)


def test_recv_message_zmqlet(mocker):
    zmqlet1 = Zmqlet(args1, default_logger)
    zmqlet2 = Zmqlet(args2, default_logger)
    req = Request()
    req.request_id = random_identity()
    doc = req.data.docs.add()
    doc.tags['id'] = 2
    msg = Message(None, req, 'tmp', '')

    def callback(msg_):
        assert msg_.request.docs[0].tags['id'] == msg.request.data.docs[0].tags['id']

    mock = mocker.Mock()
    zmqlet1.send_message(msg)
    time.sleep(1)
    zmqlet2.recv_message(mock)
    validate_callback(mock, callback)
