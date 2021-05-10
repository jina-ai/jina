from collections.abc import MutableSequence
from typing import Iterable, Union, Dict

from ...helper import deprecated_class

from ..querylang import QueryLang
from ...proto.jina_pb2 import QueryLangProto

from ..arrays.querylang import QueryLangArray

AcceptQueryLangType = Union[QueryLang, QueryLangProto, Dict]

__all__ = ['QueryLangSet', 'AcceptQueryLangType']


@deprecated_class(new_class=QueryLangArray)
class QueryLangSet(MutableSequence):
    """
    :class:`QueryLangSet` is deprecated. A new class name is QueryLangArray.
    """

    pass
