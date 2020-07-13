from .. import BaseFilterDriver


class QuerySetDriver(BaseFilterDriver):
    """
    A QuerySet represents a collection of objects from your database.
    It can have zero, one or many filters. Filters narrow down the query results
    based on the given parameters.

    In SQL terms, a QuerySet equates to a SELECT statement,
    and a filter is a limiting clause such as WHERE or LIMIT.
    """
