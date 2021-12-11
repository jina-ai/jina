from typing import Optional, List

from ..base import BaseProtoView
from ..proto import docarray_pb2


class NamedScore(BaseProtoView):
    """
    :class:`NamedScore` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.docarray_pb2.NamedScoreProto` object without working with Protobuf itself.

    To create a :class:`NamedScore` object, simply:

        .. highlight:: python
        .. code-block:: python

            from jina.types.score import NamedScore
            score = NamedScore()
            score.value = 10.0

    :class:`NamedScore` can be built from ``docarray_pb2.NamedScoreProto`` (as a weak reference or a deep copy)
    or from a set of `attributes` from ``docarray_pb2.NamedScoreProto`` passed to the constructor.
         .. highlight:: python
         .. code-block:: python

             from jina.types.score import NamedScore
             from docarray_pb2 import NamedScoreProto
             score = NamedScore(value=10.0, op_name='ranker', description='score computed by ranker')

             score_proto = NamedScoreProto()
             score_proto.value = 10.0
             score = NamedScore(score_proto)

    :param score: The score to construct from, depending on the ``copy``,
        it builds a view or a copy from it.
    :type score: Optional[docarray_pb2.NamedScoreProto]
    :param copy: When ``score`` is given as a :class:`NamedScoreProto` object, build a
        view (i.e. weak reference) from it or a deep copy from it.
    :type copy: bool
    :param kwargs: Other parameters to be set

    """

    _PbMsg = docarray_pb2.NamedScoreProto

    def __init__(self, obj=None, copy: bool = False, **kwargs):
        super().__init__(obj, copy=copy)
        self._set_attrs(**kwargs)
        if self._pb_body is None:
            raise ValueError(f'{type(self)} can not be initialized as empty')

    def _set_attrs(self, **kwargs):
        """Update fields with key-value specified in kwargs.

        :param kwargs: Key-value parameters to be set
        """
        for k, v in kwargs.items():
            if isinstance(v, (list, tuple)):
                self._pb_body.ClearField(k)
                if k == 'operands':
                    scores_to_add = []
                    for item in v:
                        if isinstance(item, NamedScore):
                            score_to_add = item
                        elif isinstance(item, docarray_pb2.NamedScoreProto):
                            score_to_add = NamedScore(item)
                        elif isinstance(item, dict):
                            score_to_add = NamedScore(**item)
                        else:
                            raise AttributeError(f'{item} is not recognized.')
                        scores_to_add.append(score_to_add)

                    for score_to_add in scores_to_add:
                        s = self._pb_body.operands.add()
                        s.CopyFrom(score_to_add._pb_body)
                else:
                    raise AttributeError(
                        f'{k} is not recognized, the only list argument is operands'
                    )
            else:
                if (
                    hasattr(NamedScore, k)
                    and isinstance(getattr(NamedScore, k), property)
                    and getattr(NamedScore, k).fset
                ):
                    # if class property has a setter
                    setattr(self, k, v)
                elif hasattr(self._pb_body, k):
                    # no property setter, but proto has this attribute so fallback to proto
                    setattr(self._pb_body, k, v)
                else:
                    raise AttributeError(f'{k} is not recognized')

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
    def operands(self: 'NamedScore') -> List['NamedScore']:
        """Returns list of nested NamedScore operands.

        :return: list of nested NamedScore operands.
        """
        return [type(self)(operand) for operand in self._pb_body.operands]
