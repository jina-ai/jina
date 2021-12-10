from typing import Optional, List

from ..base import BaseProtoType


class ScoreView(BaseProtoType):
    """
    :class:`NamedScore` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.NamedScoreProto` object without working with Protobuf itself.

    To create a :class:`NamedScore` object, simply:

        .. highlight:: python
        .. code-block:: python

            from jina.types.score import NamedScore
            score = NamedScore()
            score.value = 10.0

    :class:`NamedScore` can be built from ``jina_pb2.NamedScoreProto`` (as a weak reference or a deep copy)
    or from a set of `attributes` from ``jina_pb2.NamedScoreProto`` passed to the constructor.
         .. highlight:: python
         .. code-block:: python

             from jina.types.score import NamedScore
             from jina_pb2 import NamedScoreProto
             score = NamedScore(value=10.0, op_name='ranker', description='score computed by ranker')

             score_proto = NamedScoreProto()
             score_proto.value = 10.0
             score = NamedScore(score_proto)

    :param score: The score to construct from, depending on the ``copy``,
        it builds a view or a copy from it.
    :type score: Optional[jina_pb2.NamedScoreProto]
    :param copy: When ``score`` is given as a :class:`NamedScoreProto` object, build a
        view (i.e. weak reference) from it or a deep copy from it.
    :type copy: bool
    :param kwargs: Other parameters to be set

    """

    @property
    def value(self) -> float:
        """Return the ``value`` of this NamedScore, the `id` of which this NamedScore is a score.

        :return: the score value
        """
        return self._pb_body.value

    @value.setter
    def value(self, val: float):
        """Set the ``value`` to :attr:`value`.

        :param val: The score value to set
        """
        self._pb_body.value = val

    @property
    def ref_id(self) -> str:
        """Return the ``ref_id`` of this NamedScore, the `id` of which this NamedScore is a score.

        :return: the ref_id
        """
        return self._pb_body.ref_id

    @ref_id.setter
    def ref_id(self, val: str):
        """
        Set the ``ref_id`` to :param: `val`.
        :param val: The ref_id value to set
        """
        self._pb_body.ref_id = val

    @property
    def op_name(self) -> str:
        """Return the ``op_name`` of this NamedScore

        :return: the op_name
        """
        return self._pb_body.op_name

    @op_name.setter
    def op_name(self, val: str):
        """Set the ``op_name`` to :param: `val`.

        :param val: The op_name value to set
        """
        self._pb_body.op_name = val

    @property
    def description(self) -> str:
        """Return the ``description`` of this NamedScore

        :return: the description
        """
        return self._pb_body.description

    @description.setter
    def description(self, val: str):
        """Set the ``description`` to :param: `val`.

        :param val: The description value to set
        """
        self._pb_body.description = val

    @property
    def operands(self: 'ScoreView') -> List['ScoreView']:
        """Returns list of nested NamedScore operands.

        :return: list of nested NamedScore operands.
        """
        return [type(self)(operand) for operand in self._pb_body.operands]
