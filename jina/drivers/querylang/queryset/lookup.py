"""

Originally from https://github.com/naiquevin/lookupy

The library is provided as-is under the MIT License

Copyright (c) 2013 Vineet Naik (naikvin@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

import re

from .dunderkey import dunder_get, dunder_partition, undunder_keys, dunder_truncate
from .helper import *
from typing import Dict, Iterable, Any


class QuerySet:
    """Provides an interface to filter data and select specific fields
    from the data

    QuerySet is used for filtering data and also selecting only
    relevant fields out of it. This object is internally created which
    means usually you, the user wouldn't need to create it.

    :param data: an iterable of dicts

    """

    def __init__(self, data):
        self.data = data

    def filter(self, *args, **kwargs) -> 'QuerySet':
        """Filters data using the _lookup parameters

        Lookup parameters can be passed as,

          1. keyword arguments of type `field__lookuptype=value` where
             lookuptype specifies how to "query" eg::

                 >>> c.items.filter(language__contains='java')

             above will match all items where the language field
             contains the substring 'java' such as 'java',
             'javascript'. Each look up is treated as a conditional
             clause and if multiple of them are passed, they are
             combined using logical the ``and`` operator

             For nested fields, double underscore can be used eg::

                 >>> data = [{'a': {'b': 3}}, {'a': {'b': 10}}]
                 >>> c = Collection(data)
                 >>> c.items.filter(a__b__gt=5)

             above _lookup will match the 2nd element (b > 5)

             For the list of supported _lookup parameter, see
             documentation on Github

          2. pos arguments of the type ``field__lookuptype=Q(...)``.
             These can be useful to build conditional clauses that
             need to be combined using logical `or` or negated using
             `not`

                 >>> c.items.filter(Q(language__exact='Python')
                                    |
                                    Q(language__exact='Ruby')

             above query will only filter the data where language is
             either 'Python' or 'Ruby'

        For more documentation see README on Github

        :param args   : ``Q`` objects
        :param kwargs : _lookup parameters
        :rtype        : QuerySet

        """
        return self.__class__(filter_items(self.data, *args, **kwargs))

    def select(self, *args, **kwargs) -> 'QuerySet':
        """Selects specific fields of the data

        e.g. to select just the keys 'framework' and 'type' from many
        keys, ::

            >>> c.items.select('framework', 'type')


        :param args   : field names to select
        :param kwargs : optional keyword args

        """
        flatten = kwargs.pop('flatten', False)
        f = dunder_truncate if flatten else undunder_keys
        result = (f(d) for d in include_keys(self.data, args))
        return self.__class__(result)

    def __iter__(self):
        for d in self.data:
            yield d


# QuerySet given an alias for backward compatibility
Collection = QuerySet


## filter and _lookup functions

def filter_items(items: Iterable, *args, **kwargs) -> Iterable:
    """Filters an iterable using _lookup parameters

    :param items  : iterable
    :param args   : ``Q`` objects
    :param kwargs : _lookup parameters
    :rtype        : lazy iterable (generator)

    """
    q1 = list(args) if args else []
    q2 = [Q(**kwargs)] if kwargs else []
    lookup_groups = q1 + q2
    pred = lambda item: all(lg.evaluate(item) for lg in lookup_groups)
    return (item for item in items if pred(item))


def _lookup(key: str, val: Any, item: Dict) -> bool:
    """Checks if key-val pair exists in item using various _lookup types

    The _lookup types are derived from the `key` and then used to check
    if the _lookup holds true for the item::

        >>> _lookup('request__url__exact', 'http://example.com', item)

    The above will return True if item['request']['url'] ==
    'http://example.com' else False

    :param key  : (str) that represents the field name to find
    :param val  : (mixed) object to match the value in the item against
    :param item : (dict)
    :rtype      : (boolean) True if field-val exists else False

    """
    init, last = dunder_partition(key)
    if last == 'exact':
        return dunder_get(item, init) == val
    elif last == 'neq':
        return dunder_get(item, init) != val
    elif last == 'contains':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: val in y)
    elif last == 'icontains':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: val.lower() in y.lower())
    elif last == 'in':
        val = guard_iter(val)
        return dunder_get(item, init) in val
    elif last == 'startswith':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: y.startswith(val))
    elif last == 'istartswith':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: y.lower().startswith(val.lower()))
    elif last == 'endswith':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: y.endswith(val))
    elif last == 'iendswith':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: y.lower().endswith(val.lower()))
    elif last == 'gt':
        return iff_not_none(dunder_get(item, init), lambda y: y > val)
    elif last == 'gte':
        return iff_not_none(dunder_get(item, init), lambda y: y >= val)
    elif last == 'lt':
        return iff_not_none(dunder_get(item, init), lambda y: y < val)
    elif last == 'lte':
        return iff_not_none(dunder_get(item, init), lambda y: y <= val)
    elif last == 'regex':
        return iff_not_none(dunder_get(item, init), lambda y: re.search(val, y) is not None)
    elif last == 'filter':
        val = guard_Q(val)
        result = guard_iter(dunder_get(item, init))
        return len(list(filter_items(result, val))) > 0
    else:
        return dunder_get(item, key) == val


## Classes to compose compound lookups (Q object)

class LookupTreeElem:
    """Base class for a child in the _lookup expression tree"""

    def __init__(self):
        self.negate = False

    def evaluate(self, item: Dict) -> bool:
        raise NotImplementedError

    def __or__(self, other):
        node = LookupNode()
        node.op = 'or'
        node.add_child(self)
        node.add_child(other)
        return node

    def __and__(self, other):
        node = LookupNode()
        node.add_child(self)
        node.add_child(other)
        return node


class LookupNode(LookupTreeElem):
    """A node (element having children) in the _lookup expression tree

    Typically it's any object composed of two ``Q`` objects eg::

        >>> Q(language__neq='Ruby') | Q(framework__startswith='S')
        >>> ~Q(language__exact='PHP')

    """

    def __init__(self):
        super().__init__()
        self.children = []
        self.op = 'and'

    def add_child(self, child):
        self.children.append(child)

    def evaluate(self, item: Dict) -> bool:
        """Evaluates the expression represented by the object for the item

        :param item : (dict) item
        :rtype      : (boolean) whether _lookup passed or failed

        """
        results = map(lambda x: x.evaluate(item), self.children)
        result = any(results) if self.op == 'or' else all(results)
        return not result if self.negate else result

    def __invert__(self):
        newnode = LookupNode()
        for c in self.children:
            newnode.add_child(c)
        newnode.negate = not self.negate
        return newnode


class LookupLeaf(LookupTreeElem):
    """Class for a leaf in the _lookup expression tree"""

    def __init__(self, **kwargs):
        super().__init__()
        self.lookups = kwargs

    def evaluate(self, item: Dict) -> bool:
        """Evaluates the expression represented by the object for the item

        :param item : (dict) item
        :rtype      : (boolean) whether _lookup passed or failed

        """
        result = all(_lookup(k, v, item) for k, v in self.lookups.items())
        return not result if self.negate else result

    def __invert__(self):
        newleaf = LookupLeaf(**self.lookups)
        newleaf.negate = not self.negate
        return newleaf


# alias LookupLeaf to Q
Q = LookupLeaf


## functions that work on the keys in a dict

def include_keys(items: Iterable[Dict[str, Any]], fields: Iterable[str]) -> Iterable[Dict]:
    """Function to keep only specified fields in data

    Returns a list of dict with only the keys mentioned in the
    `fields` param::

        >>> include_keys(items, ['request__url', 'response__status'])

    Note: the resulting keys are "dundered", as they appear in `fields`,
    rather than nested as they are in `items`.

    :param items  : iterable of dicts
    :param fields : (iterable) fieldnames to keep
    :rtype        : lazy iterable

    """
    return ({f: dunder_get(item, f) for f in fields} for item in items)


guard_Q = partial(guard_type, Q)
