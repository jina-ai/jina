from collections.abc import MutableSequence
from typing import Iterable, Union, Dict

from ...helper import deprecated_class

from ..querylang import QueryLang
from ...proto.jina_pb2 import QueryLangProto

from ..lists.querylang import QueryLangList

AcceptQueryLangType = Union[QueryLang, QueryLangProto, Dict]

__all__ = ['QueryLangSet', 'AcceptQueryLangType']


@deprecated_class(new_class=QueryLangList)
class QueryLangSet(MutableSequence):
    """
    :class:`QueryLangSet` is deprecated. A new class name is QueryLangList.
    """

    pass
