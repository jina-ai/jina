from abc import abstractmethod

from jina import DocumentArray
from ...proto import jina_pb2


class DocsPropertyMixin:
    """Mixin class of docs property."""

    @abstractmethod
    def body(self):
        """Requred body property

        .. # noqa: DAR201
        """
        ...

    @property
    def docs(self) -> 'DocumentArray':
        """Get the :class: `DocumentArray` with sequence `body.docs` as content.

        .. # noqa: DAR201"""
        self.is_used = True
        return DocumentArray(self.body.docs)


class GroundtruthPropertyMixin:
    """Mixin class of groundtruths property."""

    @abstractmethod
    def body(self):
        """Requred body property

        .. # noqa: DAR201
        """
        ...

    @property
    def groundtruths(self) -> 'DocumentArray':
        """Get the groundtruths in :class: `DocumentArray` type.

        .. # noqa: DAR201"""
        self.is_used = True
        return DocumentArray(self.body.groundtruths)


class CommandMixin:
    """Mixin class of command property."""

    @abstractmethod
    def proto(self):
        """Requred proto property

        .. # noqa: DAR201
        """
        ...

    @property
    def command(self) -> str:
        """Get the command.

        .. #noqa: DAR201"""
        self.is_used = True
        return jina_pb2.RequestProto.ControlRequestProto.Command.Name(
            self.proto.control.command
        )
