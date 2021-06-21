import pytest

from jina.peapods.runtimes.zmq.base import ZMQRuntime
from jina.peapods.zmq import Zmqlet
from jina.parsers import set_pod_parser
from jina.types.message import Message
from jina.clients.request import request_generator
from tests import random_docs
from jina import __default_executor__


@pytest.fixture
def zmq_args_argparse():
    args = [
        '--name',
        'test2',
        '--uses-before',
        __default_executor__,
        '--parallel',
        '1',
        '--host',
        '0.0.0.0',
        '--port-expose',
        '45678',
        '--timeout-ctrl',
        '5000',
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture
def zmq_args_dict(zmq_args_argparse):
    return vars(zmq_args_argparse)


@pytest.fixture
def runtime(zmq_args_argparse):
    return ZMQRuntime(args=zmq_args_argparse, ctrl_addr='')


@pytest.fixture
def ctrl_messages():
    return [
        Message(None, r, 'test', '123') for r in request_generator('/', random_docs(10))
    ]


@pytest.fixture(params=['zmq_args_dict', 'zmq_args_argparse'])
def test_init(request):
    runtime = ZMQRuntime(args=request.param, ctrl_addr='')
    assert runtime.host == '0.0.0.0'
    assert runtime.port_expose == 45678


def test_status(runtime, ctrl_messages, mocker):
    mocker.patch('jina.peapods.runtimes.zmq.base.send_ctrl_message', return_value=123)
    assert runtime.status == 123


def test_is_ready(runtime, ctrl_messages, mocker):
    mocker.patch(
        'jina.peapods.runtimes.zmq.base.send_ctrl_message',
        return_value=ctrl_messages[0],
    )
    assert runtime.is_ready is False


@pytest.mark.parametrize('host', ['pi@192.0.0.1', '192.0.0.1'])
def test_get_ctrl_addr(host):
    assert Zmqlet.get_ctrl_address(host, 56789, False)[0] == 'tcp://192.0.0.1:56789'


@pytest.mark.parametrize('host', ['pi@192.0.0.1', '192.0.0.1'])
def test_get_ctrl_addr_ipc(host):
    assert Zmqlet.get_ctrl_address(host, 56789, True)[0].startswith('ipc')
