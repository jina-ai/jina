__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from collections import Iterable
from functools import partial


## Exceptions

class LookupyError(Exception):
    """Base exception class for all exceptions raised by lookupy"""
    pass


## utility functions

def iff(precond, val, f):
    """If and only if the precond is True

    Shortcut function for precond(val) and f(val). It is mainly used
    to create partial functions for commonly required preconditions

    :param precond : (function) represents the precondition
    :param val     : (mixed) value to which the functions are applied
    :param f       : (function) the actual function

    """
    return False if not precond(val) else f(val)


iff_not_none = partial(iff, lambda x: x is not None)


def guard_type(classinfo, val):
    if not isinstance(val, classinfo):
        raise LookupyError(f'Value not a {classinfo}')
    return val


guard_str = partial(guard_type, str)
guard_iter = partial(guard_type, Iterable)
guard_int = partial(guard_type, int)
