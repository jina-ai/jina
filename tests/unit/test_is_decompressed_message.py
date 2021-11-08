import time

from jina.helper import random_identity
from jina.logging.predefined import default_logger
from jina.parsers import set_pea_parser
from jina.peapods.runtimes.zmq.zed import ZEDRuntime
from jina.peapods.peas import BasePea
from jina.peapods.zmq import Zmqlet
from jina.types.message import Message
from jina.types.request import Request
from jina import Executor, requests
from tests import validate_callback


class DecompressExec(Executor):
    @requests()
    def func(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'used'


class MockRuntimeNotDecompressed(ZEDRuntime):
    def _post_hook(self, msg: 'Message'):
        super()._post_hook(msg)
        if msg is not None:
            decompressed = msg.request.is_decompressed
            if msg.is_data_request:
                assert not decompressed
        return msg


class MockRuntimeDecompressed(ZEDRuntime):
    def _post_hook(self, msg: 'Message'):
        super()._post_hook(msg)
        if msg is not None:
            decompressed = msg.request.is_decompressed
            if msg.is_data_request:
                assert decompressed
        return msg


class MockPea(BasePea):
    def _get_runtime_cls(self):
        if self.args.runtime_cls == 'MockRuntimeNotDecompressed':
            return MockRuntimeNotDecompressed
        else:
            return MockRuntimeDecompressed


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
        '--runtime-cls',
        'MockRuntimeNotDecompressed',
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
        'DecompressExec',
        '--runtime-cls',
        'MockRuntimeDecompressed',
    ]
)


def test_not_decompressed_zmqlet(mocker):
    with MockPea(args2) as pea, Zmqlet(args1, default_logger) as z:
        req = Request()
        req.request_id = random_identity()
        d = req.data.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')
        mock = mocker.Mock()
        z.send_message(msg)
        time.sleep(1)
        z.recv_message(mock)

    def callback(msg_):
        pass

    validate_callback(mock, callback)
    print(f' joining pea')
    pea.join()
    print(f' joined pea')


def test_decompressed_zmqlet(mocker):
    with MockPea(args3) as pea, Zmqlet(args1, default_logger) as z:
        req = Request()
        req.request_id = random_identity()
        d = req.data.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')

        mock = mocker.Mock()
        z.send_message(msg)
        time.sleep(1)
        z.recv_message(mock)

    def callback(msg_):
        pass

    validate_callback(mock, callback)
    print(f' joining pea')
    pea.join()
    print(f' joined pea')


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
