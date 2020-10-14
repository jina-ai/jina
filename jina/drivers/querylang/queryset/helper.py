from functools import partial
from typing import Callable, List, Type, Union, Iterable


## Exceptions

class LookupyError(Exception):
    """Base exception class for all exceptions raised by lookupy"""
    pass


## utility functions

def iff(precond: Callable, val: Union[int, str], f: Callable) -> bool:
    """If and only if the precond is True

    Shortcut function for precond(val) and f(val). It is mainly used
    to create partial functions for commonly required preconditions

    :param precond : (function) represents the precondition
    :param val     : (mixed) value to which the functions are applied
    :param f       : (function) the actual function

    """
    return False if not precond(val) else f(val)


iff_not_none = partial(iff, lambda x: x is not None)


def guard_type(classinfo: Union[Type[str], Type[Iterable]], val: Union[str, List[int]]) -> Union[str, List[int]]:
    if not isinstance(val, classinfo):
        raise LookupyError(f'Value not a {classinfo}')
    return val


guard_str = partial(guard_type, str)
guard_iter = partial(guard_type, Iterable)
guard_int = partial(guard_type, int)
