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


from typing import Tuple, Dict, Any, Optional

from google.protobuf.struct_pb2 import Struct

from .helper import *


def dunderkey(*args: str) -> str:
    """Produces a nested key from multiple args separated by double
    underscore

       >>> dunderkey('a', 'b', 'c')
       >>> 'a__b__c'

    :param args: the multiple strings
    :return:: the joined key
    """
    return '__'.join(args)


def dunder_partition(key: str) -> Tuple[str, Optional[str]]:
    """Split a dunderkey into 2 parts.

    The first part is everything before the final double underscore
    The second part is after the final double underscore

        >>> dunder_partition('a__b__c')
        >>> ('a__b', 'c')

    :param key : the dunder string
    :return: the two parts

    """
    part1: str
    part2: Optional[str]
    try:
        part1, part2 = key.rsplit('__', 1)
    except ValueError:
        part1, part2 = key, None
    return part1, part2


def dunder_init(key: str) -> str:
    """Returns the initial part of the dunder key

        >>> dunder_init('a__b__c')
        >>> 'a__b'

    :param key : the dunder string
    :return: the first part (None if invalid dunder str)
    """
    return dunder_partition(key)[0]


def dunder_last(key: str) -> Optional[str]:
    """Returns the last part of the dunder key

        >>> dunder_last('a__b__c')
        >>> 'c'

    :param key : the dunder string
    :return: the last part (None if invalid dunder string)
    """
    return dunder_partition(key)[1]


def dunder_get(_dict: Any, key: str) -> Any:
    """Returns value for a specified dunderkey

    A "dunderkey" is just a fieldname that may or may not contain
    double underscores (dunderscores!) for referencing nested keys in
    a dict. eg::

         >>> data = {'a': {'b': 1}}
         >>> dunder_get(data, 'a__b')
         1

    key 'b' can be referrenced as 'a__b'

    :param _dict : (dict, list, struct or object) which we want to index into
    :param key   : (str) that represents a first level or nested key in the dict
    :return: (mixed) value corresponding to the key

    """

    try:
        part1, part2 = key.split('__', 1)
    except ValueError:
        part1, part2 = key, ''

    try:
        part1 = int(part1)  # parse int parameter
    except ValueError:
        pass

    if isinstance(part1, int):
        result = guard_iter(_dict)[part1]
    elif isinstance(_dict, (dict, Struct)):
        if part1 in _dict:
            result = _dict[part1]
        else:
            result = None
    else:
        result = getattr(_dict, part1)

    return dunder_get(result, part2) if part2 else result


def undunder_keys(_dict: Dict) -> Dict:
    """Returns dict with the dunder keys converted back to nested dicts

    eg::

        >>> undunder_keys({'a': 'hello', 'b__c': 'world'})
        {'a': 'hello', 'b': {'c': 'world'}}

    :param _dict : (dict) flat dict
    :return: (dict) nested dict

    """

    def f(keys, value):
        """
        Recursively undunder the keys.

        :param keys: keys to undunder
        :param value: related value
        :return: undundered keys
        """
        return {keys[0]: f(keys[1:], value)} if keys else value

    def merge(dict1, dict2):
        """
        Merge second dictionary into the first one.

        :param dict1: dictionary which gets modified
        :param dict2: dictionary to read from
        """
        key, val = list(dict2.items())[0]

        if key in dict1:
            merge(dict1[key], val)
        else:
            dict1[key] = val

    result = {}
    for k, v in _dict.items():
        merge(result, f(k.split('__'), v))

    return result


def dunder_truncate(_dict: Dict) -> Dict:
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
    :return: (dict) flattened result

    """
    keylist = list(_dict.keys())

    def decide_key(k, klist):
        """
        Get the truncated key.

        :param k: One element of key list.
        :param klist: List of current keys.
        :return: Original k if truncated key is not unique else return truncated key.
        """
        newkey = dunder_last(k)
        return newkey if list(map(dunder_last, klist)).count(newkey) == 1 else k

    original_keys = [decide_key(key, keylist) for key in keylist]
    return dict(zip(original_keys, _dict.values()))
