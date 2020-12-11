from typing import Optional


from ...excepts import BadNamedScoreType
from ...proto import jina_pb2

__all__ = ['NamedScore']


class NamedScore:

    def __init__(self, score: Optional[jina_pb2.NamedScoreProto] = None,
                 copy: bool = False, **kwargs):
        self._score = jina_pb2.NamedScoreProto()
        try:
            if isinstance(score, jina_pb2.NamedScoreProto):
                if copy:
                    self._score.CopyFrom(score)
                else:
                    self._score = score
        except Exception as ex:
            raise BadNamedScoreType(f'fail to construct a NamedScore from {score}') from ex

        self.set_attrs(**kwargs)

    def __getattr__(self, name: str):
        return getattr(self._score, name)

    def set_attrs(self, **kwargs):
        """Bulk update Document fields with key-value specified in kwargs

        .. seealso::
            :meth:`get_attrs` for bulk get attributes

        """
        for k, v in kwargs.items():
            if isinstance(v, list) or isinstance(v, tuple):
                self._score.ClearField(k)
                getattr(self._score, k).extend(v)
            elif isinstance(v, dict):
                self._score.ClearField(k)
                getattr(self._score, k).update(v)
            else:
                if hasattr(NamedScore, k) and isinstance(getattr(NamedScore, k), property) and getattr(NamedScore,
                                                                                                       k).fset:
                    # if class property has a setter
                    setattr(self, k, v)
                elif hasattr(self._score, k):
                    # no property setter, but proto has this attribute so fallback to proto
                    setattr(self._score, k, v)
                else:
                    raise AttributeError(f'{k} is not recognized')
