import traceback
from typing import Optional, Dict, TYPE_CHECKING

from jina.serve.executors import BaseExecutor
from jina.proto import jina_pb2
from jina.types.mixin import ProtoTypeMixin

if TYPE_CHECKING:
    from docarray import DocumentArray


class Request(ProtoTypeMixin):
    """
    :class:`Request` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.RequestProto` object without working with Protobuf itself.

    A container for serialized :class:`jina_pb2.RequestProto` that only triggers deserialization
    and decompression when receives the first read access to its member.

    It overrides :meth:`__getattr__` to provide the same get/set interface as an
    :class:`jina_pb2.RequestProto` object.

    :param request: The request.
    """

    def __getattr__(self, name: str):
        return getattr(self.proto, name)

    @property
    def docs(self) -> 'DocumentArray':
        """Get the documents attached with the Request
        :return: documents attached to the Request
        """
        return self.proto.docs

    @docs.setter
    def docs(self, docs: 'DocumentArray'):
        self.proto.docs = docs

    @property
    def parameters(self) -> Dict:
        """Get the parameters attached with the Request
        :return: parameters attached to the Request.
        """
        return self.proto.parameters

    @parameters.setter
    def parameters(self, parameters: Dict):
        self.proto.parameters = parameters

    def add_exception(
        self, ex: Optional['Exception'] = None, executor: 'BaseExecutor' = None
    ) -> None:
        """Add exception to the last route in the envelope
        :param ex: Exception to be added
        :param executor: Executor related to the exception
        """
        d = self.header.status
        d.code = jina_pb2.StatusProto.ERROR
        d.description = repr(ex)

        if executor:
            d.exception.executor = executor.__class__.__name__
        d.exception.name = ex.__class__.__name__
        d.exception.args.extend([str(v) for v in ex.args])
        d.exception.stacks.extend(
            traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)
        )
