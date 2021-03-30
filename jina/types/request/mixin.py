from ..lists import DocumentList
from ...proto import jina_pb2


class DocsPropertyMixin:
    """Mixin class of docs property."""

    @property
    def docs(self) -> 'DocumentList':
        """Get the :class: `DocumentList` with sequence `body.docs` as content."""
        self.is_used = True
        return DocumentList(self.body.docs)


class GroundtruthPropertyMixin:
    """Mixin class of groundtruths property."""

    @property
    def groundtruths(self) -> 'DocumentList':
        """Get the groundtruths in :class: `DocumentList` type."""
        self.is_used = True
        return DocumentList(self.body.groundtruths)


class IdsMixin:
    """Mixin class of ids property."""

    @property
    def ids(self):
        """Get the ids."""
        return self.body.ids


class CommandMixin:
    """Mixin class of command property."""

    @property
    def command(self) -> str:
        """Get the command."""
        self.is_used = True
        return jina_pb2.RequestProto.ControlRequestProto.Command.Name(
            self.proto.control.command
        )
