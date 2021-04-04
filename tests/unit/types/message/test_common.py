import pytest
from jina.clients.request import request_generator
from jina.enums import RequestType

from jina.proto import jina_pb2
from jina.types.message.common import ControlMessage
from jina.types.request.control import ControlRequest


@pytest.mark.parametrize('command', ['IDLE', 'CANCEL', 'TERMINATE', 'STATUS', 'RELOAD'])
def test_control_msg(command):
    msg = ControlMessage(command)
    assert msg.proto.envelope.request_type == 'ControlRequest'
    assert msg.request.control.command == getattr(
        jina_pb2.RequestProto.ControlRequestProto, command
    )
    assert msg.request.command == command


def test_bad_control_command():
    with pytest.raises(ValueError):
        ControlMessage('hello world')


def test_control_reload():
    for r in request_generator(
        None, mode=RequestType.CONTROL, command='RELOAD', devices='pod0'
    ):
        assert isinstance(r, ControlRequest)
        assert r.command == 'RELOAD'
        assert r.args['devices'] == 'pod0'
