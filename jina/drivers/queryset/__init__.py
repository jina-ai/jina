from typing import List

from .. import BaseDriver


class QuerySetDriver(BaseDriver):
    """
    A QuerySet represents a collection of objects from your database.
    It can have zero, one or many filters. Filters narrow down the query results
    based on the given parameters.

    In SQL terms, a QuerySet equates to a SELECT statement,
    and a filter is a limiting clause such as WHERE or LIMIT.
    """

    def __init__(self, queryset_raw: List[str] = None, combine_policy: str = 'append', *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(queryset_raw, List) and queryset_raw:
            self.queryset_raw = queryset_raw
        elif isinstance(queryset_raw, str):
            self.queryset_raw = [queryset_raw]
        else:
            self.queryset_raw = []
        self.combine_policy = combine_policy

    def __call__(self, *args, **kwargs):
        q = getattr(self.req, 'queryset_raw', None)
        if isinstance(q, str):
            q = [q]
        if q:
            if self.combine_policy == 'append':
                self.queryset_raw.extend(q)
            elif self.combine_policy == 'prepend':
                self.queryset_raw = q + self.queryset_raw
            elif self.combine_policy == 'override':
                self.queryset_raw = q

        for d in self.execute():
            pass

    def execute(self):
        pass
