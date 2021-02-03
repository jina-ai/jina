from typing import Optional

from ..mixin import ProtoTypeMixin
from ...excepts import BadNamedScoreType
from ...helper import typename
from ...proto import jina_pb2

__all__ = ['NamedScore']


class NamedScore(ProtoTypeMixin):
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

     """

    def __init__(self, score: Optional[jina_pb2.NamedScoreProto] = None,
                 copy: bool = False, **kwargs):
        """

        :param score: the score to construct from, depending on the ``copy``,
                it builds a view or a copy from it.
        :param copy: when ``score`` is given as a :class:`NamedScoreProto` object, build a
                view (i.e. weak reference) from it or a deep copy from it.
        :param kwargs: other parameters to be set
        """
        self._pb_body = jina_pb2.NamedScoreProto()
        try:
            if isinstance(score, jina_pb2.NamedScoreProto):
                if copy:
                    self._pb_body.CopyFrom(score)
                else:
                    self._pb_body = score
            elif score is not None:
                # note ``None`` is not considered as a bad type
                raise ValueError(f'{typename(score)} is not recognizable')
        except Exception as ex:
            raise BadNamedScoreType(f'fail to construct a NamedScore from {score}') from ex

        self.set_attrs(**kwargs)

    def set_attrs(self, **kwargs):
        """Bulk update Document fields with key-value specified in kwargs

        .. seealso::
            :meth:`get_attrs` for bulk get attributes

        """
        for k, v in kwargs.items():
            if isinstance(v, list) or isinstance(v, tuple):
                self._pb_body.ClearField(k)
                getattr(self._pb_body, k).extend(v)
            elif isinstance(v, dict):
                self._pb_body.ClearField(k)
                getattr(self._pb_body, k).update(v)
            else:
                if hasattr(NamedScore, k) and isinstance(getattr(NamedScore, k), property) and getattr(NamedScore,
                                                                                                       k).fset:
                    # if class property has a setter
                    setattr(self, k, v)
                elif hasattr(self._pb_body, k):
                    # no property setter, but proto has this attribute so fallback to proto
                    setattr(self._pb_body, k, v)
                else:
                    raise AttributeError(f'{k} is not recognized')
