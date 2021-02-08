__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import sys
import time
from collections import defaultdict
from functools import wraps

from ..helper import colored, get_readable_size, get_readable_time

if False:
    # fix type-hint complain for sphinx and flake
    from . import JinaLogger


def used_memory(unit: int = 1024 * 1024 * 1024) -> float:
    """
    Get the memory usage of the current process.

    :param unit: Unit of the memory, default in Gigabytes.
    :return: Memory usage of the current process.
    """
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / unit
    except ModuleNotFoundError:
        from . import default_logger
        default_logger.error('module "resource" can not be found and you are likely running it on Windows, '
                             'i will return 0')
        return 0


def used_memory_readable() -> str:
    """
    Get the memory usage of the current process in a human-readable format.

    :return: Memory usage of the current process.
    """
    return get_readable_size(used_memory(1))


def profiling(func):
    """
    Create the Decorator to mark a function for profiling. The time and memory usage will be recorded and printed.

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
        start_mem = used_memory(unit=1)
        r = func(*args, **kwargs)
        elapsed = time.perf_counter() - start_t
        end_mem = used_memory(unit=1)
        # level_prefix = ''.join('-' for v in inspect.stack() if v and v.index is not None and v.index >= 0)
        level_prefix = ''
        mem_status = f'memory Δ {get_readable_size(end_mem - start_mem)} {get_readable_size(start_mem)} -> {get_readable_size(end_mem)}'
        default_logger.info(f'{level_prefix} {func.__qualname__} time: {elapsed}s {mem_status}')
        return r

    return arg_wrapper


class TimeDict:
    """Records of time information."""

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
        """
        Clear the time information.

        :return: None
        """
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
        return ' '.join(f'{k}: {v:3.1f}s' for k, v in self.accum_time.items())


class TimeContext:
    """Timing a code snippet with a context manager."""

    time_attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']

    def __init__(self, task_name: str, logger: 'JinaLogger' = None):
        """
        Create the context manager to timing a code snippet.

        :param task_name: The context/message.
        :param logger: Use existing logger or use naive :func:`print`.

        Example:
        .. highlight:: python
        .. code-block:: python

            with TimeContext('loop'):
                do_busy()

        """
        self.task_name = task_name
        self._logger = logger
        self.duration = 0

    def __enter__(self):
        self.start = time.perf_counter()
        self._enter_msg()
        return self

    def _enter_msg(self):
        if self._logger:
            self._logger.info(self.task_name + '...')
        else:
            print(self.task_name, end=' ...\t', flush=True)

    def __exit__(self, typ, value, traceback):
        self.duration = self.now()

        self.readable_duration = get_readable_time(seconds=self.duration)

        self._exit_msg()

    def now(self) -> float:
        return time.perf_counter() - self.start

    def _exit_msg(self):
        if self._logger:
            self._logger.info(f'{self.task_name} takes {self.readable_duration} ({self.duration:.2f}s)')
        else:
            print(colored(f'    {self.readable_duration} ({self.duration:.2f}s)', 'green'), flush=True)


class ProgressBar(TimeContext):
    """
    A simple progress bar.

    Example:
        .. highlight:: python
        .. code-block:: python

            with ProgressBar('loop'):
                do_busy()
    """

    def __init__(self, bar_len: int = 20, task_name: str = '', batch_unit: str = 'batch', logger=None):
        """
        Create the ProgressBar.

        :param bar_len: Total length of the bar.
        :param task_name: The name of the task, will be displayed in front of the bar.
        :param batch_unit: Unit of batch
        :param logger: Jina logger
        """
        super().__init__(task_name, logger)
        self.bar_len = bar_len
        self.num_docs = 0
        self._ticks = 0
        self.batch_unit = batch_unit

    def update_tick(self, tick: float = .1) -> None:
        """
        Increment the progress bar by one tick, when the ticks accumulate to one, trigger one :meth:`update`.

        :param tick: A float unit to increment (should < 1).
        """
        self._ticks += tick
        if self._ticks > 1:
            self.update()
            self._ticks = 0

    def update(self, progress: int = None, *args, **kwargs) -> None:
        """
        Increment the progress bar by one unit.

        :param progress: The number of unit to increment.
        """
        self.num_reqs += 1
        sys.stdout.write('\r')
        elapsed = time.perf_counter() - self.start
        num_bars = self.num_reqs % self.bar_len
        num_bars = self.bar_len if not num_bars and self.num_reqs else max(num_bars, 1)
        if progress:
            self.num_docs += progress

        sys.stdout.write(
            '{:>10} |{:<{}}| 📃 {:6d} ⏱️ {:3.1f}s 🐎 {:3.1f}/s {:6d} {:>10}'.format(
                colored(self.task_name, 'cyan'),
                colored('█' * num_bars, 'green'),
                self.bar_len + 9,
                self.num_docs,
                elapsed,
                self.num_docs / elapsed,
                self.num_reqs,
                self.batch_unit
            ))
        if num_bars == self.bar_len:
            sys.stdout.write('\n')
        sys.stdout.flush()
        from . import profile_logger
        profile_logger.info({'num_bars': num_bars,
                             'num_reqs': self.num_reqs,
                             'bar_len': self.bar_len,
                             'progress': num_bars / self.bar_len,
                             'task_name': self.task_name,
                             'qps': self.num_reqs / elapsed,
                             'speed': (self.num_docs if self.num_docs > 0 else self.num_reqs) / elapsed,
                             'speed_unit': ('Documents' if self.num_docs > 0 else 'Requests'),
                             'elapsed': elapsed})

    def __enter__(self):
        super().__enter__()
        self.num_reqs = -1
        self.num_docs = 0
        self.update()
        return self

    def _enter_msg(self):
        pass

    def _exit_msg(self):
        if self.num_docs > 0:
            speed = self.num_docs / self.duration
        else:
            speed = self.num_reqs / self.duration
        sys.stdout.write(f'\t{colored(f"✅ done in ⏱ {self.readable_duration} 🐎 {speed:3.1f}/s", "green")}\n')
