__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

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

## This module deals with code regarding handling the double
## underscore separated keys
from .helper import *


def dunderkey(*args):
    """Produces a nested key from multiple args separated by double
    underscore

       >>> dunderkey('a', 'b', 'c')
       >>> 'a__b__c'

    :param *args : *String
    :rtype       : String
    """
    return '__'.join(args)


def dunder_partition(key):
    """Splits a dunderkey into 2 parts

    The first part is everything before the final double underscore
    The second part is after the final double underscore

        >>> dunder_partition('a__b__c')
        >>> ('a__b', 'c')

    :param neskey : String
    :rtype        : 2 Tuple

    """
    parts = key.rsplit('__', 1)
    return tuple(parts) if len(parts) > 1 else (parts[0], None)


def dunder_init(key):
    """Returns the initial part of the dunder key

        >>> dunder_init('a__b__c')
        >>> 'a__b'

    :param neskey : String
    :rtype        : String
    """
    return dunder_partition(key)[0]


def dunder_last(key):
    """Returns the last part of the dunder key

        >>> dunder_last('a__b__c')
        >>> 'c'

    :param neskey : String
    :rtype        : String
    """
    return dunder_partition(key)[1]


def dunder_get(_dict, key):
    """Returns value for a specified dunderkey

    A "dunderkey" is just a fieldname that may or may not contain
    double underscores (dunderscores!) for referrencing nested keys in
    a dict. eg::

         >>> data = {'a': {'b': 1}}
         >>> nesget(data, 'a__b')
         1

    key 'b' can be referrenced as 'a__b'

    :param _dict : (dict)
    :param key   : (str) that represents a first level or nested key in the dict
    :rtype       : (mixed) value corresponding to the key

    """
    parts = key.split('__', 1)

    try:
        parts[0] = int(parts[0])  # parse int parameter
    except ValueError:
        pass

    if isinstance(parts[0], int):
        result = guard_iter(_dict)[parts[0]]
    else:
        result = getattr(_dict, parts[0])
    return result if len(parts) == 1 else dunder_get(result, parts[1])


def undunder_keys(_dict):
    """Returns dict with the dunder keys converted back to nested dicts

    eg::

        >>> undunder_keys({'a': 'hello', 'b__c': 'world'})
        {'a': 'hello', 'b': {'c': 'world'}}

    :param _dict : (dict) flat dict
    :rtype       : (dict) nested dict

    """

    def f(key, value):
        parts = key.split('__')
        return {
            parts[0]: value if len(parts) == 1 else f(parts[1], value)
        }

    result = {}
    for r in [f(k, v) for k, v in _dict.items()]:
        rk = list(r.keys())[0]
        if rk not in result:
            result.update(r)
        else:
            result[rk].update(r[rk])
    return result


def dunder_truncate(_dict):
    """Returns dict with dunder keys truncated to only the last part

    In other words, replaces the dunder keys with just last part of
    it. In case many identical last parts are encountered, they are
    not truncated further

    eg::

        >>> dunder_truncate({'a__p': 3, 'b__c': 'no'})
        {'c': 'no', 'p': 3}
        >>> dunder_truncate({'a__p': 'yay', 'b__p': 'no', 'c__z': 'dunno'})
        {'a__p': 'yay', 'b__p': 'no', 'z': 'dunno'}

    :param _dict : (dict) to flatten
    :rtype       : (dict) flattened result

    """
    keylist = list(_dict.keys())

    def decide_key(k, klist):
        newkey = dunder_last(k)
        return newkey if list(map(dunder_last, klist)).count(newkey) == 1 else k

    original_keys = [decide_key(key, keylist) for key in keylist]
    return dict(zip(original_keys, _dict.values()))
