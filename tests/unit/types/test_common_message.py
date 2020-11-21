import pytest

from jina.proto import jina_pb2
from jina.types.message.common import ControlMessage


@pytest.mark.parametrize('command', ['IDLE', 'TERMINATE', 'STATUS'])
def test_control_msg(command):
    msg = ControlMessage(command)
    assert msg.as_pb_object.envelope.request_type == 'ControlRequest'
    assert msg.request.control.command == getattr(jina_pb2.RequestProto.ControlRequestProto, command)
    assert msg.request.command == command


def test_bad_control_command():
    with pytest.raises(ValueError):
        ControlMessage('hello world')
