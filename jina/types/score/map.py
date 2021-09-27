from collections.abc import MutableMapping
from typing import Optional, Union

import numpy as np

from ..score import NamedScore
from ...helper import typename
from ...proto import jina_pb2

__all__ = ['NamedScoreMapping']

if False:
    from google.protobuf.pyext._message import MessageMapContainer


class NamedScoreMapping(MutableMapping):
    """
    :class:`NamedScoreMapping` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.NamedScoreMappingProto` object without working with Protobuf itself.

    It offers an interface to access and update scores as `NamedScore` as values of a `dict` with a string key.

    To create a :class:`NamedScoreMappingProto` object, simply:

        .. highlight:: python
        .. code-block:: python

            from jina.types.score.map import NamedScoreMapping
            scores = NamedScoreMapping()
            scores['score'] = 50

    :class:`NamedScoreMapping` can be built from ``jina_pb2.NamedScoreMappingProto`` (as a weak reference or a deep copy)

    :param scores: The scores to construct from, depending on the ``copy``,
        it builds a view or a copy from it.
    :type score: Optional[jina_pb2.NamedScoreMappingProto]
    :param copy: When ``scores`` is given as a :class:`NamedScoreMappingProto` object, build a
        view (i.e. weak reference) from it or a deep copy from it.
    :type copy: bool
    :param kwargs: Other parameters to be set

    """

    def __init__(
        self,
        scores: 'MessageMapContainer',
    ):
        self._pb_body = scores

    def __setitem__(
        self,
        key: str,
        value: Union[jina_pb2.NamedScoreProto, NamedScore, float, np.generic],
    ):
        if isinstance(value, jina_pb2.NamedScoreProto):
            self._pb_body[key].CopyFrom(value)
        elif isinstance(value, NamedScore):
            self._pb_body[key].CopyFrom(value._pb_body)
        elif isinstance(value, (float, int)):
            self._pb_body[key].value = value
        elif isinstance(value, np.generic):
            self._pb_body[key].value = value.item()
        else:
            raise TypeError(f'score is in unsupported type {typename(value)}')

    def __getitem__(
        self,
        key: str,
    ):
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
