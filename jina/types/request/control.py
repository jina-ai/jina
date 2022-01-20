from typing import Optional

from jina.types.request import Request
from jina.helper import typename, random_identity
from jina.proto import jina_pb2

_available_commands = dict(jina_pb2.ControlRequestProto.DESCRIPTOR.enum_values_by_name)


class ControlRequest(Request):
    """
    :class:`ControlRequest` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.ControlRequestProto` object without working with Protobuf itself.

    A container for serialized :class:`jina_pb2.ControlRequestProto` that only triggers deserialization
    and decompression when receives the first read access to its member.

    It overrides :meth:`__getattr__` to provide the same get/set interface as an
    :class:`jina_pb2.ControlRequestProtoProto` object.

    :param command: the command for this request, can be STATUS, ACTIVATE or DEACTIVATE
    :param request: The request.
    """

    def __init__(
        self,
        command: Optional[str] = None,
        request: Optional['jina_pb2.jina_pb2.ControlRequestProto'] = None,
    ):

        if isinstance(request, jina_pb2.ControlRequestProto):
            self._pb_body = request
        elif request is not None:
            # note ``None`` is not considered as a bad type
            raise ValueError(f'{typename(request)} is not recognizable')
        if command:
            proto = jina_pb2.ControlRequestProto()
            proto.header.request_id = random_identity()
            if command in _available_commands:
                proto.command = getattr(jina_pb2.ControlRequestProto, command)
            else:
                raise ValueError(
                    f'command "{command}" is not supported, must be one of {_available_commands}'
                )
            self._pb_body = proto

    def add_related_entity(
        self, id: str, address: str, port: int, shard_id: Optional[int] = None
    ):
        """
        Add a related entity to this ControlMessage

        :param id: jina id of the entity
        :param address: address of the entity
        :param port: Port of the entity
        :param shard_id: Optional id of the shard this entity belongs to
        """
        self.proto.relatedEntities.append(
            jina_pb2.RelatedEntity(id=id, address=address, port=port, shard_id=shard_id)
        )

    @property
    def proto(self) -> 'jina_pb2.ControlRequestProto':
        """
        Cast ``self`` to a :class:`jina_pb2.ControlRequestProto`. Laziness will be broken and serialization will be recomputed when calling
        :meth:`SerializeToString`.
        :return: protobuf instance
        """
        return self._pb_body

    @property
    def command(self) -> str:
        """Get the command.

        .. #noqa: DAR201"""
        return jina_pb2.ControlRequestProto.Command.Name(self.proto.command)
