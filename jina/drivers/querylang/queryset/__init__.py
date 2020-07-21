__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from .. import BaseQueryLangDriver


class QuerySetDriver(BaseQueryLangDriver):
    """
    A QuerySet represents a collection of objects from your database.
    It can have zero, one or many filters. Filters narrow down the query results
    based on the given parameters.

    In SQL terms, a QuerySet equates to a SELECT statement,
    and a filter is a limiting clause such as WHERE or LIMIT.
    """
