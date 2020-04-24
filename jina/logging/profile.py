__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import time
from collections import defaultdict
from functools import wraps

from ..helper import colored

if False:
    # fix type-hint complain for sphinx and flake
    import logging


def used_memory(unit: int = 1024 * 1024 * 1024) -> float:
    """Get the memory usage of the current process and all sub-processes.

    :param unit: unit of the memory, default in Gigabytes
    """
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / unit
    except ModuleNotFoundError:
        from . import default_logger
        default_logger.error('module "resource" can not be found and you are likely running it on Windows, '
                             'i will return 0')
        return 0


def profiling(func):
    """Decorator to mark a function for profiling. The time and memory usage will be recorded and printed.

    Example:

    .. highlight:: python
    .. code-block:: python

        @profiling
        def foo():
            print(1)

    """
    from . import default_logger

    @wraps(func)
    def arg_wrapper(*args, **kwargs):
        start_t = time.perf_counter()
        start_mem = used_memory(unit=1024 * 1024)
        r = func(*args, **kwargs)
        elapsed = time.perf_counter() - start_t
        end_mem = used_memory(unit=1024 * 1024)
        # level_prefix = ''.join('-' for v in inspect.stack() if v and v.index is not None and v.index >= 0)
        level_prefix = ''
        mem_status = 'memory Δ %4.2fMB %4.2fMB -> %4.2fMB' % (end_mem - start_mem, start_mem, end_mem)
        default_logger.info('%s%s time: %3.3fs %s' % (level_prefix, func.__qualname__, elapsed, mem_status))
        return r

    return arg_wrapper


class TimeDict:
    def __init__(self):
        self.accum_time = defaultdict(float)
        self.first_start_time = defaultdict(float)
        self.start_time = defaultdict(float)
        self.end_time = defaultdict(float)
        self._key_stack = []
        self._pending_reset = False

    def __enter__(self):
        _key = self._key_stack[-1]
        # store only the first enter time
        if _key not in self.first_start_time:
            self.first_start_time[_key] = time.perf_counter()
        self.start_time[_key] = time.perf_counter()
        return self

    def __exit__(self, typ, value, traceback):
        _key = self._key_stack.pop()
        self.end_time[_key] = time.perf_counter()
        self.accum_time[_key] += self.end_time[_key] - self.start_time[_key]
        if self._pending_reset:
            self.reset()

    def __call__(self, key: str, *args, **kwargs):
        self._key_stack.append(key)
        return self

    def reset(self):
        if self._key_stack:
            self._pending_reset = True
        else:
            self.accum_time.clear()
            self.start_time.clear()
            self.first_start_time.clear()
            self.end_time.clear()
            self._key_stack.clear()
            self._pending_reset = False

    def __str__(self):
        return ' '.join('%s: %3.1fs' % (k, v) for k, v in self.accum_time.items())


class TimeContext:
    """Timing a code snippet with a context manager """

    def __init__(self, msg: str, logger: 'logging.Logger' = None):
        """

        :param msg: the context/message
        :param logger: use existing logger or use naive :func:`print`

        Example:

        .. highlight:: python
        .. code-block:: python

            with TimeContext('loop'):
                do_busy()

        """
        self._msg = msg
        self._logger = logger
        self.duration = 0

    def __enter__(self):
        self.start = time.perf_counter()
        if self._logger:
            self._logger.info(self._msg + '...')
        else:
            print(self._msg, end=' ...\t', flush=True)
        return self

    def __exit__(self, typ, value, traceback):
        self.duration = time.perf_counter() - self.start
        if self._logger:
            self._logger.info('%s takes %3.3f secs' % (self._msg, self.duration))
        else:
            print(colored('    [%3.3f secs]' % self.duration, 'green'), flush=True)
