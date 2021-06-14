from typing import Optional, Union

import numpy as np

from ..score import NamedScore
from ..mixin import ProtoTypeMixin
from ...excepts import BadNamedScoreType
from ...helper import typename
from ...proto import jina_pb2

__all__ = ['MappedNamedScore']


class MappedNamedScore(ProtoTypeMixin):

    """"""

    def __init__(
        self,
        scores: Optional[jina_pb2.MappedNamedScoreProto] = None,
        copy: bool = False,
        **kwargs,
    ):
        self._pb_body = jina_pb2.MappedNamedScoreProto()
        try:
            if isinstance(scores, jina_pb2.MappedNamedScoreProto):
                if copy:
                    self._pb_body.CopyFrom(scores)
                else:
                    self._pb_body = scores
            elif scores is not None:
                # note ``None`` is not considered as a bad type
                raise ValueError(f'{typename(scores)} is not recognizable')
        except Exception as ex:
            raise BadNamedScoreType(
                f'fail to construct a MappedNamedScore from {scores}'
            ) from ex

    def __setitem__(
        self,
        key: str,
        value: Union[jina_pb2.NamedScoreProto, NamedScore, float, np.generic],
    ):
        if isinstance(value, jina_pb2.NamedScoreProto):
            self._pb_body.values[key].CopyFrom(value)
        elif isinstance(value, NamedScore):
            self._pb_body.values[key].CopyFrom(value._pb_body)
        elif isinstance(value, (float, int)):
            self._pb_body.values[key].value = value
        elif isinstance(value, np.generic):
            self._pb_body.values[key].value = value.item()
        else:
            raise TypeError(f'score is in unsupported type {typename(value)}')

    def __getitem__(
        self,
        key: str,
    ):
        return NamedScore(self._pb_body.values[key])

    def __delitem__(
        self,
        key: str,
    ):
        del self._pb_body.values[key]
