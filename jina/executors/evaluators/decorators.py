"""Decorators and wrappers designed for wrapping :class:`BaseExecutor` functions. """

from functools import wraps
from typing import Callable


def as_aggregator(func: Callable) -> Callable:
    """Mark a function so that it keeps track of the number of documents evaluated and a running sum
    to have always access to average value
    """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        f = func(self, *args, **kwargs)
        self.num_documents += 1
        self.sum += f
        return f

    return arg_wrapper
