from ..sets import DocumentSet
from ...proto import jina_pb2


class DocsPropertyMixin:
    @property
    def docs(self) -> 'DocumentSet':
        self.is_used = True
        return DocumentSet(self.body.docs)


class GroundtruthPropertyMixin:
    @property
    def groundtruths(self) -> 'DocumentSet':
        self.is_used = True
        return DocumentSet(self.body.groundtruths)


class IdsMixin:
    @property
    def ids(self):
        return self.body.ids


class CommandMixin:
    @property
    def command(self) -> str:
        self.is_used = True
        return jina_pb2.RequestProto.ControlRequestProto.Command.Name(self.proto.control.command)
