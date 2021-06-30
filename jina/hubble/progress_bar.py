import sys
import time
import math
from collections import deque

from datetime import timedelta
from typing import Optional
from ..logging.profile import TimeContext
from ..helper import colored, get_readable_size, get_readable_time


class ProgressBar(TimeContext):
    """
    A simple progress bar.

    Example:
        .. highlight:: python
        .. code-block:: python

            with ProgressBar('loop') as bar:
                do_busy()

    :param task_name: The name of the task, will be displayed in front of the bar.
    :param total: Number of steps in the bar. Defaults to 100.
    :param bar_len: Total length of the bar.
    :param logger: Jina logger
    """

    window_size = 5  # average window size
    suffix = '%(percent).2f %% eta: %(eta_td)s'
    bar_prefix = ' |'
    bar_suffix = '| '
    empty_fill = ' '
    fill = '#'

    def __init__(
        self,
        task_name: str,
        total: float = 100.0,
        bar_len: int = 32,
        logger=None,
        **kwargs,
    ):
        super().__init__(task_name, logger)
        self.task_name = task_name
        self.total = total
        self.bar_len = bar_len

        self.average = 0
        self._avg_queue = deque(maxlen=self.window_size)

        self._avg_update_ts = None
        self._update_ts = None

        for key, val in kwargs.items():
            setattr(self, key, val)

    def __getitem__(self, key):
        if key.startswith('_'):
            return None
        return getattr(self, key, None)

    @property
    def remaining(self):
        """Return the remaining steps to be completed

        :return: the remaining steps
        """
        return max(self.total - self.completed, 0)

    @property
    def elapsed(self):
        """Return the elapsed time

        :return: the elapsed seconds
        """
        return int(time.perf_counter() - self.start)

    @property
    def elapsed_td(self) -> 'timedelta':
        """Return the timedelta of elapsed time

        :return: the timedelta of elapsed seconds
        """
        return timedelta(seconds=self.elapsed)

    @property
    def eta(self):
        """Return EAT (estimated time of arrival)

        :return: return the seconds of ETA
        """
        return math.ceil(self.avg * self.remaining)

    @property
    def eta_td(self) -> 'timedelta':
        """Return the timedelta of ETA

        :return: the timedelta of ETA
        """
        return timedelta(seconds=self.eta)

    @property
    def percent(self) -> float:
        """Calculate percentage complete.

        :return: the percentage of completed
        """
        return self.completed / self.total * 100

    def update_avg(self, steps: float, dt: float):
        """Update the average of speed
        :param steps: the completed steps
        :param dt: the time seconds to use
        """
        if steps > 0:
            win_len = len(self._avg_queue)
            self._avg_queue.append(dt / steps)
            now = time.perf_counter()

            if win_len < self.window_size or now - self._avg_update_ts > 1:
                self.avg = sum(self._avg_queue) / len(self._avg_queue)
                self._avg_update_ts = now

    def update(
        self,
        steps: Optional[float] = 1.0,
        completed: Optional[float] = None,
        total: Optional[float] = None,
        suffix_msg: Optional[str] = None,
    ):
        """Update progress with new values.

        :param steps: Number of incremental completed steps.
        :param completed: : Number of completed steps.
        :param total: Total number of steps, or `None` to not change. Defaults to None.
        :param suffix_msg: the suffix message
        """

        now = time.perf_counter()
        if completed is not None:
            steps = max(0, completed - self.completed)
            self.completed = completed
        else:
            self.completed += steps

        self.update_avg(steps, now - self._update_ts)
        self._update_ts = now

        self.total = total if total is not None else self.total

        num_bars = int(max(1, self.percent / 100 * self.bar_len))
        num_bars = num_bars % self.bar_len
        num_bars = self.bar_len if not num_bars and self.completed else max(num_bars, 1)

        sys.stdout.write('\r')

        suffix = (suffix_msg or self.suffix) % self
        line = ''.join(
            [
                '⏳ {:>10}'.format(colored(self.task_name, 'cyan')),
                self.bar_prefix,
                colored(self.fill * num_bars, 'green'),
                self.empty_fill * (self.bar_len - num_bars),
                self.bar_suffix,
                suffix,
            ]
        )
        sys.stdout.write(line)
        # if num_bars == self.bar_len:
        #     sys.stdout.write('\n')
        sys.stdout.flush()

    def __enter__(self):
        super().__enter__()
        self.completed = -1
        self._update_ts = self.start
        self._avg_update_ts = self.start
        self.update()
        return self

    def _enter_msg(self):
        pass

    def _exit_msg(self):
        sys.stdout.write(
            f'\t{colored(f"✅ done in ⏱ {self.readable_duration}", "green")}\n'
        )


class ChargingBar(ProgressBar):
    """Charging Bar"""

    bar_prefix = ' '
    bar_suffix = ' '
    empty_fill = '∙'
    fill = '█'


class Spinner(TimeContext):
    """Spinner"""

    phases = ('-', '\\', '|', '/')

    def __enter__(self):
        super().__enter__()
        self.completed = -1
        import threading

        self._completed = threading.Event()

        self._thread = threading.Thread(target=self.running, daemon=True)
        self._thread.start()

        return self

    def __exit__(self, typ, value, traceback):
        super().__exit__(typ, value, traceback)
        self._completed.set()
        self._thread.join()

    def running(self):
        """daemon thread to output spinner"""
        while not self._completed.is_set():
            self.completed += 1
            i = self.completed % len(self.phases)
            sys.stdout.write('\r')
            line = ' '.join(
                ['⏳ {:>10}'.format(colored(self.task_name, 'cyan')), self.phases[i]]
            )
            sys.stdout.write(line)
            sys.stdout.flush()
            time.sleep(0.5)

    def update(self, **kwargs):
        """Update the progress bar

        :param kwargs: parameters that can be accepted
        """
        pass

    def _exit_msg(self):
        sys.stdout.write(
            f'\t{colored(f"✅ done in ⏱ {self.readable_duration}", "green")}\n'
        )


class PieSpinner(Spinner):
    """PieSpinner"""

    phases = ['◷', '◶', '◵', '◴']
