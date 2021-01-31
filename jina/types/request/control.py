from . import Request

from ...proto import jina_pb2


class ControlRequest(Request):
    @property
    def command(self) -> str:
        self.is_used = True
        return jina_pb2.RequestProto.ControlRequestProto.Command.Name(self.as_pb_object.control.command)
