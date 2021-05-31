from typing import Optional

from ..mixin import ProtoTypeMixin
from ...excepts import BadNamedScoreType
from ...helper import typename
from ...proto import jina_pb2

__all__ = ['GraphRelatedInfo']


class GraphRelatedInfo(ProtoTypeMixin):
    """
    :class:`GraphRelatedInfo` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.GraphRelatedInfProto` object without working with Protobuf itself.

    To create a :class:`NamedScore` object, simply:

        .. highlight:: python
        .. code-block:: python

            from jina.types.graph import GraphRelatedInfo
            graph_info = GraphRelatedInfo()

    :class:`GraphRelatedInfo` can be built from ``jina_pb2.GraphRelatedInfProto`` (as a weak reference or a deep copy)
    or from a set of `attributes` from ``jina_pb2.GraphRelatedInfProto`` passed to the constructor.
         .. highlight:: python
         .. code-block:: python

             from jina.types.score import GraphRelatedInfo
             from jina_pb2 import GraphRelatedInfProto
             graph_info = GraphRelatedInfo(adjacency=..., edge_features=...)

    :param graph_info: The graph info to construct from, depending on the ``copy``,
        it builds a view or a copy from it.
    :type graph_info: Optional[jina_pb2.GraphRelatedInfProto]
    :param copy: When ``graph_info`` is given as a :class:`GraphRelatedInfProto` object, build a
        view (i.e. weak reference) from it or a deep copy from it.
    :type copy: bool
    :param kwargs: Other parameters to be set

    """

    def __init__(
        self,
        graph_info: Optional[jina_pb2.GraphRelatedInfoProto] = None,
        copy: bool = False,
        **kwargs,
    ):
        self._pb_body = jina_pb2.GraphRelatedInfoProto()
        try:
            if isinstance(graph_info, jina_pb2.GraphRelatedInfoProto):
                if copy:
                    self._pb_body.CopyFrom(graph_info)
                else:
                    self._pb_body = graph_info
            elif graph_info is not None:
                # note ``None`` is not considered as a bad type
                raise ValueError(f'{typename(graph_info)} is not recognizable')
        except Exception as ex:
            raise BadNamedScoreType(
                f'fail to construct a GraphRelatedInfo from {graph_info}'
            ) from ex

        self.set_attrs(**kwargs)

    @property
    def value(self) -> float:
        """
        Return the ``value`` of this NamedScore, the `id` of which this NamedScore is a score.
        :return:: the score value
        """
        return self._pb_body.value

    @value.setter
    def value(self, val: float):
        """
        Set the ``value`` to :attr:`value`.
        :param val: The score value to set
        """
        self._pb_body.value = val

    def set_attrs(self, **kwargs):
        """Update GraphRelatedInfo fields with key-value specified in kwargs.

        :param kwargs: Key-value parameters to be set
        """
        for k, v in kwargs.items():
            print(f' Set for GraphRelatedInfo {k} to {v}')
