from typing import Iterator, Optional

from .. import BaseDriver
from ...proto import jina_pb2


class BaseFilterDriver(BaseDriver):
    def __init__(self, raw_filter=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if raw_filter:
            self.driver_filter = self.parse(raw_filter)

    def __call__(self, *args, **kwargs):
        f = getattr(self.req, 'raw_filter', None)
        query_filter = self.parse(f) if f else None
        filtered = self.execute(self.req.docs, self.driver_filter, query_filter)
        if filtered is None:
            # filter is done in-place.
            pass
        elif isinstance(filtered, Iterator):
            for d in filtered:
                _d = self.req.docs.add()
                _d.CopyFrom(d)

    def parse(self, raw_filter):
        raise NotImplementedError

    def execute(self, docs: Iterator['jina_pb2.Document'], driver_filter, query_filter) -> Optional[
        Iterator['jina_pb2.Document']]:
        """

        :param docs: the document to be filtered
        :param driver_filter: the parsed filter assigned to the driver
        :param query_filter: the parsed filter carried on the query
        :return: either an iterator of document,
        """
        raise NotImplementedError


class QuerySetDriver(BaseFilterDriver):
    """
    A QuerySet represents a collection of objects from your database.
    It can have zero, one or many filters. Filters narrow down the query results
    based on the given parameters.

    In SQL terms, a QuerySet equates to a SELECT statement,
    and a filter is a limiting clause such as WHERE or LIMIT.
    """


class GraphQLDriver(BaseFilterDriver):
    """
    GraphQL as in-memory filter
    """


class CythonFilterDriver(BaseFilterDriver):
    """
    Cython implementation of the in-memory proto filter
    """
