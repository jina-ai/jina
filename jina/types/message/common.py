from . import Message
from ..request import Request
from ...proto import jina_pb2

_available_commands = dict(jina_pb2.RequestProto.ControlRequestProto.DESCRIPTOR.enum_values_by_name)

__all__ = ['ControlMessage']


class ControlMessage(Message):
    def __init__(self, command: str, pod_name: str = 'ctl', identity: str = '',
                 *args, **kwargs):
        req = Request(jina_pb2.RequestProto())
        if command in _available_commands:
            req.control.command = getattr(jina_pb2.RequestProto.ControlRequestProto, command)
        else:
            raise ValueError(f'command "{command}" is not supported, must be one of {_available_commands}')
        super().__init__(None, req, pod_name=pod_name, identity=identity, *args, **kwargs)
        req.request_type = 'control'
