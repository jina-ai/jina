from . import Message
from ..request import Request
from ...proto import jina_pb2

_available_commands = dict(jina_pb2.RequestProto.ControlRequestProto.DESCRIPTOR.enum_values_by_name)

__all__ = ['ControlMessage']


class ControlMessage(Message):
    """
    Class of the protobuf message.

    :param command: Command with string content. (e.g. 'IDLE', 'TERMINATE', 'STATUS')
    :param pod_name: Name of the current pod.
    :param identity: The identity of the current pod
    :param args: Additional positional arguments.
    :param kwargs: Additional keyword arguments.
    """
    def __init__(self, command: str, pod_name: str = 'ctl', identity: str = '',
                 *args, **kwargs):
        """Set constructor method."""
        req = Request(jina_pb2.RequestProto())
        if command in _available_commands:
            req.control.command = getattr(jina_pb2.RequestProto.ControlRequestProto, command)
        else:
            raise ValueError(f'command "{command}" is not supported, must be one of {_available_commands}')
        super().__init__(None, req, pod_name=pod_name, identity=identity, *args, **kwargs)
        req.request_type = 'control'
