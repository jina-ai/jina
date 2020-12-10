import numbers
from typing import Dict, Optional, TypeVar

from google.protobuf import json_format

from ...excepts import BadNamedScoreType
from ...proto import jina_pb2

__all__ = ['NamedScore', 'NamedScoreSourceType']

NamedScoreSourceType = TypeVar('NamedScoreSourceType',
                               jina_pb2.NamedScoreProto, Dict, numbers.Number)


class NamedScore:

    def __init__(self, score: Optional[NamedScoreSourceType] = None,
                 copy: bool = False, **kwargs):
        self._score = jina_pb2.NamedScoreProto()
        try:
            if isinstance(score, jina_pb2.NamedScoreProto):
                if copy:
                    self._score.CopyFrom(score)
                else:
                    self._score = score
            elif isinstance(score, Dict):
                json_format.ParseDict(score, self._score)
            elif isinstance(score, numbers.Number):
                self._score.value = score
        except Exception as ex:
            raise BadNamedScoreType(f'fail to construct a NamedScore from {score}') from ex

    def __getattr__(self, name: str):
        return getattr(self._score, name)

    def __str__(self):
        return f'{self.as_pb_object}'

    @property
    def op_name(self):
        return self._score.op_name

    @op_name.setter
    def op_name(self, op_name: str):
        self._score.op_name = op_name

    @property
    def value(self):
        return self._score.value

    @value.setter
    def value(self, value: float):
        self._score.value = value

    @property
    def description(self):
        return self._score.description

    @description.setter
    def description(self, description: str):
        self._score.description = description

    @property
    def ref_id(self):
        return self._score.ref_id

    @ref_id.setter
    def ref_id(self, ref_id: str):
        self._score.ref_id = ref_id
