import warnings
from typing import TypeVar, Dict, Optional, Type

from google.protobuf import json_format

from ...drivers import BaseDriver
from ...excepts import BadQueryLangType
from ...helper import typename
from ...importer import import_classes
from ...proto import jina_pb2

QueryLangSourceType = TypeVar('QueryLangSourceType',
                              jina_pb2.QueryLangProto, bytes, str, Dict, BaseDriver)

__all__ = ['QueryLang']


class QueryLang:
    """
    :class:`QueryLang` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.QueryLangProto` object without working with Protobuf itself.

    To create a :class:`QueryLang` object from a :class:`BaseDriver` object, simply:

        .. highlight:: python
        .. code-block:: python

            from jina import QueryLang
            from jina.drivers.querylang.slice import SliceQL

            s = SliceQL(start=3, end=4)
            ql = QueryLang(s)

    One can also build a :class`QueryLang` from JSON string, bytes, dict or directly from a protobuf object.

    A :class:`QueryLang` object (no matter how it is constructed) can be converted to
    protobuf object or back to driver object by using:

        .. highlight:: python
        .. code-block:: python

            # to protobuf object
            s.as_pb_object

            # to driver object
            s.as_driver_object

    To get the class name of the associated driver, one can use :attr:`driver`.

    """

    def __init__(self, querylang: Optional[QueryLangSourceType] = None, copy: bool = False):
        """

        :param querylang: the query language source to construct from, acceptable types include:
            :class:`jina_pb2.QueryLangProto`, :class:`bytes`, :class:`str`, :class:`Dict`, :class:`BaseDriver`.
        :param copy: when ``querylang`` is given as a :class:`QueryLangProto` object, build a
                view (i.e. weak reference) from it or a deep copy from it.
        """
        self._querylang = jina_pb2.QueryLangProto()
        try:
            if isinstance(querylang, jina_pb2.QueryLangProto):
                if copy:
                    self._querylang.CopyFrom(querylang)
                else:
                    self._querylang = querylang
            elif isinstance(querylang, dict):
                json_format.ParseDict(querylang, self._querylang)
            elif isinstance(querylang, str):
                json_format.Parse(querylang, self._querylang)
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
                        self._querylang.ParseFromString(querylang)
                    except RuntimeWarning as ex:
                        raise BadQueryLangType('fail to construct a query language') from ex
            elif isinstance(querylang, BaseDriver):
                self.driver = querylang
                self.priority = querylang._priority
                self._querylang.parameters.update(querylang._init_kwargs_dict)
            elif querylang is not None:
                # note ``None`` is not considered as a bad type
                raise ValueError(f'{typename(querylang)} is not recognizable')
        except Exception as ex:
            raise BadQueryLangType('fail to construct a query language') from ex

    @property
    def priority(self) -> int:
        """Get the priority of this query language. The query language only takes
        effect when if it has a higher priority than the internal one with the same name"""
        return self._querylang.priority

    @priority.setter
    def priority(self, value: int):
        self._querylang.priority = value

    @property
    def name(self) -> str:
        """Get the name of the driver that the query language attached to """
        return self._querylang.name

    @name.setter
    def name(self, value: str):
        """Set the name of the driver that the query language attached to """
        self._querylang.name = value

    @property
    def driver(self) -> Type['BaseDriver']:
        """Get the driver class that the query language attached to

        ..warning::
            This browses all module trees and can be costly,
            do not frequently call it.
        """
        return import_classes('jina.drivers', targets=[self.name])

    @driver.setter
    def driver(self, value: 'BaseDriver'):
        """Set the driver class that the query language attached to """
        self._querylang.name = value.__class__.__name__

    def __getattr__(self, name: str):
        return getattr(self._querylang, name)

    @property
    def as_pb_object(self) -> 'jina_pb2.QueryLangProto':
        """Return a protobuf :class:`jina_pb2.QueryLangProto` object """
        return self._querylang

    @property
    def as_driver_object(self) -> 'BaseDriver':
        """Return a :class:`BaseDriver` object """
        return self.driver(**self._querylang.parameters)
