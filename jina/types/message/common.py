from typing import Optional

from . import Message
from ..request import Request
from ...proto import jina_pb2

_available_commands = dict(
    jina_pb2.RequestProto.ControlRequestProto.DESCRIPTOR.enum_values_by_name
)

__all__ = ['ControlMessage']


class ControlMessage(Message):
    """
    Class of the protobuf message.

    :param command: Command with string content. (e.g. 'IDLE', 'CANCEL', 'TERMINATE', 'STATUS')
    :param args: Additional positional arguments which are just used for the parent initialization
    :param kwargs: Additional keyword arguments which are just used for the parent initialization
    """

    def __init__(self, command: str, *args, **kwargs):
        req = Request(jina_pb2.RequestProto())
        if command in _available_commands:
            req.control.command = getattr(
                jina_pb2.RequestProto.ControlRequestProto, command
            )
        else:
            raise ValueError(
                f'command "{command}" is not supported, must be one of {_available_commands}'
            )
        super().__init__(None, req, *args, **kwargs)
        req = req.as_typed_request('control')
        args = kwargs.get('args', None)
        if args:
            req.args = args

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
        self.request.body.relatedEntities.append(
            jina_pb2.RelatedEntity(id=id, address=address, port=port, shard_id=shard_id)
        )
