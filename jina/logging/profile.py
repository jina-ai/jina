import datetime
import itertools
import math
import sys
import threading
import time
from collections import defaultdict
from functools import wraps
from typing import Optional, Union, Callable

from .. import __windows__
from jina.enums import ProgressBarStatus

from .logger import JinaLogger
from ..helper import colored, get_readable_size, get_readable_time


def used_memory(unit: int = 1024 * 1024 * 1024) -> float:
    """
    Get the memory usage of the current process.

    :param unit: Unit of the memory, default in Gigabytes.
    :return: Memory usage of the current process.
    """
    if __windows__:
        # TODO: windows doesn't include `resource` module
        return 0

    import resource

    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / unit


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

    :param func: function to be profiled
    :return: arguments wrapper
    """
    from .predefined import default_logger

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
        default_logger.info(
            f'{level_prefix} {func.__qualname__} time: {elapsed}s {mem_status}'
        )
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
        """
        Add time counter.

        :param key: key name of the counter
        :param args: extra arguments
        :param kwargs: keyword arguments
        :return: self object
        """
        self._key_stack.append(key)
        return self

    def reset(self):
        """Clear the time information."""
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
        """
        Get the passed time from start to now.

        :return: passed time
        """
        return time.perf_counter() - self.start

    def _exit_msg(self):
        if self._logger:
            self._logger.info(
                f'{self.task_name} takes {self.readable_duration} ({self.duration:.2f}s)'
            )
        else:
            print(
                colored(
                    f'{self.task_name} takes {self.readable_duration} ({self.duration:.2f}s)'
                ),
                flush=True,
            )


class ProgressBar(TimeContext):
    """
    A simple progress bar.

    Example:
        .. highlight:: python
        .. code-block:: python

            with ProgressBar('loop'):
                do_busy()
    """

    col_width = 100
    clear_line = '\r{}\r'.format(' ' * col_width)
    spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])

    def __init__(
        self,
        description: str = 'Working...',
        message_on_done: Union[str, Callable[..., str], None] = None,
        final_line_feed: bool = True,
    ):
        """
        Create the ProgressBar.

        :param description: The name of the task, will be displayed in front of the bar.
        :param message_on_done: The final message to print when the progress is complete
        :param final_line_feed: if False, the line will not get a Line Feed and thus is easily overwritable.
        """
        super().__init__(description, None)
        self._bars_on_row = 40
        self._completed_progress = 0
        self._last_rendered_progress = 0
        self._num_update_called = 0
        self._on_done = message_on_done
        self._final_line_feed = final_line_feed
        self._stop_event = threading.Event()

    def update(
        self,
        progress: float = 1.0,
        description: Optional[str] = None,
        message: Optional[str] = None,
        status: ProgressBarStatus = ProgressBarStatus.WORKING,
        first_enter: bool = False,
    ) -> None:
        """
        Increment the progress bar by one unit.

        :param progress: The number of unit to increment.
        :param description: Change the description text before the progress bar on update.
        :param message: Change the message text followed after the progress bar on update.
        :param status: If set to a value, it will mark the task as complete, can be either "Done" or "Canceled"
        :param first_enter: if this method is called by `__enter__`
        """
        self._num_update_called += 0 if first_enter else 1
        self._completed_progress += progress
        self._last_rendered_progress = self._completed_progress
        elapsed = time.perf_counter() - self.start
        num_bars = self._completed_progress % self._bars_on_row
        num_bars = (
            self._bars_on_row
            if not num_bars and self._completed_progress
            else max(num_bars, 1)
        )
        num_fullbars = math.floor(num_bars)
        num_halfbars = 1 if (num_bars - num_fullbars <= 0.5) else 0

        if status in {ProgressBarStatus.DONE, ProgressBarStatus.CANCELED}:
            bar_color, unfinished_bar_color = 'yellow', 'yellow'
        elif status == ProgressBarStatus.ERROR:
            bar_color, unfinished_bar_color = 'red', 'red'
        else:
            bar_color, unfinished_bar_color = 'green', 'green'

        speed_str = (
            'estimating...'
            if first_enter
            else f'{self._num_update_called / elapsed:4.1f} step/s'
        )

        description_str = description or self.task_name or ''
        if status != ProgressBarStatus.WORKING:
            description_str = str(status)
        msg_str = message or ''
        self._bar_info = dict(
            bar_color=bar_color,
            description_str=description_str,
            msg_str=msg_str,
            num_fullbars=num_fullbars,
            num_halfbars=num_halfbars,
            speed_str=speed_str,
            unfinished_bar_color=unfinished_bar_color,
        )

    def _print_bar(self, bar_info):
        time_str = str(
            datetime.timedelta(seconds=time.perf_counter() - self.start)
        ).split('.')[0]
        sys.stdout.write(self.clear_line)
        sys.stdout.write(
            '{} {:>10} {:<}{:<} {} {} {}'.format(
                colored(next(self.spinner), 'green'),
                bar_info['description_str'],
                colored('━' * bar_info['num_fullbars'], bar_info['bar_color'])
                + (
                    colored(
                        '╸',
                        bar_info['bar_color']
                        if bar_info['num_halfbars']
                        else bar_info['unfinished_bar_color'],
                    )
                ),
                colored(
                    '━' * (self._bars_on_row - bar_info['num_fullbars']),
                    bar_info['unfinished_bar_color'],
                    attrs=['dark'],
                ),
                colored(time_str, 'cyan'),
                bar_info['speed_str'],
                bar_info['msg_str'],
            )
        )
        sys.stdout.flush()

    def _update_thread(self):
        sys.stdout.flush()
        while not self._stop_event.is_set():
            self._print_bar(self._bar_info)
            time.sleep(0.1)

    def _enter_msg(self):
        self.update(first_enter=True)

        self._progress_thread = threading.Thread(
            target=self._update_thread, daemon=True
        )
        self._progress_thread.start()

    def __exit__(self, exc_type, value, traceback):
        self.duration = self.now()

        self.readable_duration = get_readable_time(seconds=self.duration)

        if exc_type in {KeyboardInterrupt, SystemExit}:
            self._stop_event.set()
            self.update(0, status=ProgressBarStatus.CANCELED)
            self._print_bar(self._bar_info)
            return True  # prevent it from being propagated
        elif exc_type and issubclass(exc_type, Exception):
            self._stop_event.set()
            self.update(0, status=ProgressBarStatus.ERROR)
            self._print_bar(self._bar_info)
        else:
            # normal ending, i.e. task is complete
            self._stop_event.set()
            self._progress_thread.join()
            self.update(0, status=ProgressBarStatus.DONE)
            self._print_bar(self._bar_info)
            self._print_final_msg()

    def _print_final_msg(self):
        if self._last_rendered_progress > 1:
            final_msg = f'\033[K{self._completed_progress:.0f} steps done in {self.readable_duration}'
            if self._on_done:
                if isinstance(self._on_done, str):
                    final_msg = self._on_done
                elif callable(self._on_done):
                    final_msg = self._on_done()
            sys.stdout.write(final_msg)
            if self._final_line_feed:
                sys.stdout.write('\n')
        else:
            # no actual render happens
            sys.stdout.write(self.clear_line)
        sys.stdout.flush()
