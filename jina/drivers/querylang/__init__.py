__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterator, Optional, Any

from .. import BaseRecursiveDriver, BaseDriver
from ...proto import jina_pb2


class QueryLangDriver(BaseRecursiveDriver):
    """
    :class:`QueryLangDriver` allows a driver to read arguments from the protobuf message. This allows a
    driver to override its behavior based on the message it receives. Extremely useful in production, for example,
    get ``top_k`` results, doing pagination, filtering.

    To register the field you want to read from the message, simply register them in :meth:`__init__`.
    For example, ``__init__(self, arg1, arg2, **kwargs)`` will allow the driver to read field ``arg1`` and ``arg2`` from
    the message. When they are not found in the message, the value ``_arg1`` and ``_arg2`` will be used. Note the underscore
    prefix.

    .. note::
        - To set default value of ``arg1``, use ``self._arg1 = ``, note the underscore in the front.
        - To access ``arg1``, simply use ``self.arg1``. It automatically switch between default ``_arg1`` and ``arg1`` from the request.

    For successful value reading, the following condition must be met:

        - the ``name`` in the proto must match with the current class name
        - the ``disabled`` field in the proto should not be ``False``
        - the ``priority`` in the proto should be strictly greater than the driver's priority (by default is 0)
        - the field name must exist in proto's ``parameters``

    """

    def __init__(self, priority: int = 0, *args, **kwargs):
        """

        :param priority: the priority of its default arg values (hardcoded in Python). If the
        received ``QueryLang`` has a higher priority, it will override the hardcoded value
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self._priority = priority

    def _get_parameter(self, key: str, default: Any):
        for q in self.queryset:
            if (not q.disabled and self.__class__.__name__ == q.name and
                    q.priority > self._priority and key in q.parameters):
                return q.parameters[key]
        return getattr(self, f'_{key}', default)

    def __getattr__(self, name: str):
        # https://docs.python.org/3/reference/datamodel.html#object.__getattr__
        if name == '_init_kwargs_dict':
            # raise attribute error to avoid recursive call
            raise AttributeError
        if name in self._init_kwargs_dict:
            return self._get_parameter(name, default=self._init_kwargs_dict[name])


class BaseQueryLangDriver(BaseDriver):
    """
    :class:`BaseQueryLangDriver` adds native data querying capabilities to Jina,

    The following Standard Query Operator to be implemented
    - filter/where: filter the doc/chunk by its attributes
    - select/exclude: select attributes to include in the results
    - limit/take/slicing: take the first k doc/chunk
    - sort/order_by: sort the doc/chunk
    - reverse: reverse the list of collections
    """

    def __init__(self, raw_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if raw_query:
            self.driver_query = self.parse(raw_query)

    def __call__(self, *args, **kwargs):
        f = getattr(self.req, 'raw_query', None)
        req_query = self.parse(f) if f else None
        filtered = self.execute(self.req.docs, self.driver_query, req_query)
        if filtered is None:
            # filter is done in-place.
            pass
        elif isinstance(filtered, Iterator):
            # count length before
            len_before = len(self.req.docs)
            for d in filtered:
                _d = self.req.docs.add()
                _d.CopyFrom(d)
            # remove old ones
            del self.req.docs[:len_before]
        else:
            raise ValueError(f'do not support {type(filtered)} return type')

    def parse(self, raw_filter):
        raise NotImplementedError

    def execute(self, docs: Iterator['jina_pb2.Document'], driver_query, req_query) -> Optional[
        Iterator['jina_pb2.Document']]:
        """

        :param docs: the document to be filtered
        :param driver_query: the parsed filter assigned to the driver
        :param req_query: the parsed filter carried on the query
        :return: either an iterator of document,
        """
        raise NotImplementedError


class GraphQLDriver(BaseQueryLangDriver):
    """
    GraphQL as in-memory filter
    """


class CythonFilterDriver(BaseQueryLangDriver):
    """
    Cython implementation of the in-memory proto filter
    """
