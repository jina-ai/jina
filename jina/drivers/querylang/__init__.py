__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterator, Optional

from .. import BaseDriver
from ...proto import jina_pb2


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

    def execute(self, docs: Iterator['jina_pb2.DocumentProto'], driver_query, req_query) -> Optional[
        Iterator['jina_pb2.DocumentProto']]:
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
