from ..arrays import DocumentArray
from ...proto import jina_pb2


class DocsPropertyMixin:
    """Mixin class of docs property."""

    @property
    def docs(self) -> 'DocumentArray':
        """Get the :class: `DocumentArray` with sequence `body.docs` as content.
        :return: requested :class: `DocumentArray`
        """
        self.is_used = True
        return DocumentArray(self.body.docs)


class GroundtruthPropertyMixin:
    """Mixin class of groundtruths property."""

    @property
    def groundtruths(self) -> 'DocumentArray':
        """Get the groundtruths in :class: `DocumentArray` type.
        :return: requested groundtruths :class: `DocumentArray`
        """
        self.is_used = True
        return DocumentArray(self.body.groundtruths)


class IdsMixin:
    """Mixin class of ids property."""

    @property
    def ids(self):
        """Get the ids.
        :return: ids
        """
        return self.body.ids


class CommandMixin:
    """Mixin class of command property."""

    @property
    def command(self) -> str:
        """Get the command.
        :return: command
        """
        self.is_used = True
        return jina_pb2.RequestProto.ControlRequestProto.Command.Name(
            self.proto.control.command
        )
