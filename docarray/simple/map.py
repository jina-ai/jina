from collections.abc import MutableMapping
from typing import Union

import numpy as np
from google.protobuf.pyext._message import MessageMapContainer

from .score import NamedScore
from ..base import BaseProtoView
from ..helper import typename
from ..proto.docarray_pb2 import NamedScoreProto


class NamedScoreMap(BaseProtoView, MutableMapping):
    """
    It offers a Pythonic interface to allow users access and manipulate
    :class:`docarray_pb2.NamedScoreMappingProto` object without working with Protobuf itself.

    It offers an interface to access and update scores as `NamedScore` as values of a `dict` with a string key.

    To create a :class:`NamedScoreMappingProto` object, simply:

        .. highlight:: python
        .. code-block:: python

            from jina.types.score.map import NamedScoreMapping
            scores = NamedScoreMapping()
            scores['score'] = 50

    :class:`NamedScoreMapping` can be built from ``docarray_pb2.NamedScoreMappingProto`` (as a weak reference or a deep copy)

    :param scores: The scores to construct from, depending on the ``copy``,
        it builds a view or a copy from it.
    :type score: Optional[docarray_pb2.NamedScoreMappingProto]
    :param copy: When ``scores`` is given as a :class:`NamedScoreMappingProto` object, build a
        view (i.e. weak reference) from it or a deep copy from it.
    :type copy: bool
    :param kwargs: Other parameters to be set

    """

    _PbMsg = MessageMapContainer

    def __setitem__(
        self,
        key: str,
        value: Union[NamedScoreProto, NamedScore, float, np.generic],
    ):
        if isinstance(value, NamedScoreProto):
            self._pb_body[key].CopyFrom(value)
        elif isinstance(value, NamedScore):
            self._pb_body[key].CopyFrom(value._pb_body)
        elif isinstance(value, (np.generic, float, int)):
            self._pb_body[key].value = float(value)
        else:
            raise TypeError(f'value is in unsupported type {typename(value)}')

    def __getitem__(
        self,
        key: str,
    ) -> 'NamedScore':
        return NamedScore(self._pb_body[key])

    def __delitem__(
        self,
        key: str,
    ):
        del self._pb_body[key]

    def __contains__(self, key: str):
        return key in self._pb_body

    def __iter__(self):
        for key in self._pb_body:
            yield key

    def __len__(self):
        return len(self._pb_body)
