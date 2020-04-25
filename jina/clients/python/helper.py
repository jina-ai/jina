__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import sys
import time

from ...helper import colored
from ...logging import profile_logger


class ProgressBar:
    """A simple progress bar

    Example:

        .. highlight:: python
        .. code-block:: python

            with ProgressBar('loop'):
                do_busy()
    """

    def __init__(self, bar_len: int = 20, task_name: str = '', logger=None):
        """

        :param bar_len: total length of the bar
        :param task_name: the name of the task, will be displayed in front of the bar
        """
        self.bar_len = bar_len
        self.task_name = task_name
        self.num_docs = 0
        self.logger = logger

    def update(self, progress: int = None, *args, **kwargs) -> None:
        """ Increment the progress bar by one unit

        :param progress: the number of unit to increment
        """
        self.num_reqs += 1
        sys.stdout.write('\r')
        elapsed = time.perf_counter() - self.start_time
        num_bars = self.num_reqs % self.bar_len
        num_bars = self.bar_len if not num_bars and self.num_reqs else max(num_bars, 1)
        if progress:
            self.num_docs += progress

        sys.stdout.write(
            '{:>10} [{:<{}}] 📃 {:6d} ⏱️ {:3.1f}s 🐎 {:3.1f}/s {:6d} batch'.format(
                colored(self.task_name, 'cyan'),
                colored('=' * num_bars, 'green'),
                self.bar_len + 9,
                self.num_docs,
                elapsed,
                self.num_docs / elapsed,
                self.num_reqs
            ))
        if num_bars == self.bar_len:
            sys.stdout.write('\n')
        sys.stdout.flush()
        profile_logger.debug({'num_bars': num_bars,
                              'num_reqs': self.num_reqs,
                              'bar_len': self.bar_len,
                              'progress': num_bars / self.bar_len,
                              'task_name': self.task_name,
                              'qps': self.num_reqs / elapsed,
                              'speed': (self.num_docs if self.num_docs > 0 else self.num_reqs) / elapsed,
                              'speed_unit': ('Documents' if self.num_docs > 0 else 'Requests'),
                              'elapsed': elapsed})

    def __enter__(self):
        self.start_time = time.perf_counter()
        self.num_reqs = -1
        self.num_docs = 0
        self.update()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        if self.num_docs > 0:
            speed = self.num_docs / elapsed
        else:
            speed = self.num_reqs / elapsed
        sys.stdout.write('\t%s\n' % colored(f'✅ done in ⏱ {elapsed:3.1f}s 🐎 {speed:3.1f}/s', 'green'))
