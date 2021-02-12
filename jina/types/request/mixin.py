from ..sets import DocumentSet
from ...proto import jina_pb2


class DocsPropertyMixin:
    """Mixin class of docs property."""

    @property
    def docs(self) -> 'DocumentSet':
        """Get the :class: `DocumentSet` with sequence `body.docs` as content."""
        self.is_used = True
        return DocumentSet(self.body.docs)


class GroundtruthPropertyMixin:
    """Mixin class of groundtruths property."""

    @property
    def groundtruths(self) -> 'DocumentSet':
        """Get the groundtruths in :class: `DocumentSet` type."""
        self.is_used = True
        return DocumentSet(self.body.groundtruths)


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
        return jina_pb2.RequestProto.ControlRequestProto.Command.Name(self.proto.control.command)
