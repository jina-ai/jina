from . import Message
from ..request import Request
from ...proto import jina_pb2

_available_commands = dict(
    jina_pb2.RequestProto.DumpRequestProto.DESCRIPTOR.enum_values_by_name
)

__all__ = ['DumpMessage']


class DumpMessage(Message):
    """
    Class of the protobuf message.

    :param path: the path to which to dump
    :param shards: the nr of shards to which to dump
    :param pod_name: Name of the current pod.
    :param identity: The identity of the current pod
    :param args: Additional positional arguments which are just used for the parent initialization
    :param kwargs: Additional keyword arguments which are just used for the parent initialization
    """

    def __init__(
        self,
        path: str,
        shards: int,
        pod_name: str = 'ctl',
        identity: str = '',
        *args,
        **kwargs
    ):
        req = Request(jina_pb2.RequestProto())
        req.dump.path = path
        req.dump.shards = shards
        super().__init__(
            None, req, pod_name=pod_name, identity=identity, *args, **kwargs
        )
        req.request_type = 'dump'
