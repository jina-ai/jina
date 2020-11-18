from . import Message
from ...proto import jina_pb2

__all__ = ['ControlMessage']


class ControlMessage(Message):
    def __init__(self, command: 'jina_pb2.RequestProto.ControlRequestProto',
                 *args, **kwargs):
        req = jina_pb2.RequestProto()
        req.control.command = command
        super().__init__(None, req, *args, **kwargs)
