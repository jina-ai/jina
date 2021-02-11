import warnings
from typing import TypeVar, Dict, Optional

from google.protobuf import json_format

from ..mixin import ProtoTypeMixin
from ...excepts import BadQueryLangType
from ...helper import typename
from ...proto import jina_pb2

QueryLangSourceType = TypeVar('QueryLangSourceType',
                              jina_pb2.QueryLangProto, bytes, str, Dict)

__all__ = ['QueryLang']


class QueryLang(ProtoTypeMixin):
    """
    :class:`QueryLang` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.QueryLangProto` object without working with Protobuf itself.

    To create a :class:`QueryLang` object from a Dict containing the name of a :class:`BaseDriver`,
     and the parameters to override, simply:

        .. highlight:: python
        .. code-block:: python

            from jina import QueryLang
            ql = QueryLang({name: 'SliceQL', priority: 1, parameters: {'start': 3, 'end': 1}})

    .. warning::
        The `BaseDriver` needs to be a `QuerySetReader` to be able to read the `QueryLang`

    One can also build a :class`QueryLang` from JSON string, bytes, dict or directly from a protobuf object.

    A :class:`QueryLang` object (no matter how it is constructed) can be converted to
    protobuf object by using:

        .. highlight:: python
        .. code-block:: python

            # to protobuf object
            ql.as_pb_object

    :param querylang: the query language source to construct from, acceptable types include:
        :class:`jina_pb2.QueryLangProto`, :class:`bytes`, :class:`str`, :class:`Dict`, Tuple.
    :type querylang: Optional[QueryLangSourceType]
    :param copy: when ``querylang`` is given as a :class:`QueryLangProto` object, build a
        view (i.e. weak reference) from it or a deep copy from it.
    :type copy: bool
    """

    def __init__(self, querylang: Optional[QueryLangSourceType] = None, copy: bool = False):
        """Set constructor method."""
        self._pb_body = jina_pb2.QueryLangProto()
        try:
            if isinstance(querylang, jina_pb2.QueryLangProto):
                if copy:
                    self._pb_body.CopyFrom(querylang)
                else:
                    self._pb_body = querylang
            elif isinstance(querylang, dict):
                json_format.ParseDict(querylang, self._pb_body)
            elif isinstance(querylang, str):
                json_format.Parse(querylang, self._pb_body)
            elif isinstance(querylang, bytes):
                # directly parsing from binary string gives large false-positive
                # fortunately protobuf throws a warning when the parsing seems go wrong
                # the context manager below converts this warning into exception and throw it
                # properly
                with warnings.catch_warnings():
                    warnings.filterwarnings('error',
                                            'Unexpected end-group tag',
                                            category=RuntimeWarning)
                    try:
                        self._pb_body.ParseFromString(querylang)
                    except RuntimeWarning as ex:
                        raise BadQueryLangType('fail to construct a query language') from ex
            elif querylang is not None:
                # note ``None`` is not considered as a bad type
                raise ValueError(f'{typename(querylang)} is not recognizable')
        except Exception as ex:
            raise BadQueryLangType('fail to construct a query language') from ex

    @property
    def priority(self) -> int:
        """
        Get the priority of this query language.
        The query language only takes effect when if it has a higher priority than the internal one with the same name
        """
        return self._pb_body.priority

    @priority.setter
    def priority(self, value: int):
        """Set the priority of this query language with :param:`value`."""
        self._pb_body.priority = value

    @property
    def name(self) -> str:
        """Get the name of the driver that the query language attached to."""
        return self._pb_body.name

    @name.setter
    def name(self, value: str):
        """
        Set the name of the driver that the query language attached to.

        :param value: Name of the driver
        :type value: str
        """
        self._pb_body.name = value
