__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import sys
import time
from typing import Sequence

from ...helper import colored
from ...logging import profile_logger, default_logger
from ...logging.profile import TimeContext
from ...proto import jina_pb2


class ProgressBar(TimeContext):
    """A simple progress bar

    Example:

        .. highlight:: python
        .. code-block:: python

            with ProgressBar('loop'):
                do_busy()
    """

    def __init__(self, bar_len: int = 20, task_name: str = '', batch_unit: str = 'batch', logger=None):
        """

        :param bar_len: total length of the bar
        :param task_name: the name of the task, will be displayed in front of the bar
        """
        super().__init__(task_name, logger)
        self.bar_len = bar_len
        self.num_docs = 0
        self.batch_unit = batch_unit

    def update(self, progress: int = None, *args, **kwargs) -> None:
        """ Increment the progress bar by one unit

        :param progress: the number of unit to increment
        """
        self.num_reqs += 1
        sys.stdout.write('\r')
        elapsed = time.perf_counter() - self.start
        num_bars = self.num_reqs % self.bar_len
        num_bars = self.bar_len if not num_bars and self.num_reqs else max(num_bars, 1)
        if progress:
            self.num_docs += progress

        sys.stdout.write(
            '{:>10} [{:<{}}] 📃 {:6d} ⏱️ {:3.1f}s 🐎 {:3.1f}/s {:6d} {:>10}'.format(
                colored(self.task_name, 'cyan'),
                colored('=' * num_bars, 'green'),
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
        sys.stdout.write('\t%s\n' % colored(f'✅ done in ⏱ {self.readable_duration} 🐎 {speed:3.1f}/s', 'green'))


def pprint_routes(routes: Sequence['jina_pb2.Route'],
                  status: 'jina_pb2.Status' = None,
                  stack_limit: int = 3):
    """Pretty print routes with :mod:`prettytable`, fallback to :func:`print`

    :param routes: list of :class:`jina_pb2.Route` objects from Envelop
    :param status: the :class:`jina_pb2.Status` object
    :param stack_limit: traceback limit
    :return:
    """
    from textwrap import fill

    header = [colored(v, attrs=['bold']) for v in ('Pod', 'Time', 'Exception')]

    try:
        from prettytable import PrettyTable, ALL
        table = PrettyTable(field_names=header, align='l', hrules=ALL)
        add_row = table.add_row
        visualize = print
    except (ModuleNotFoundError, ImportError):
        default_logger.warning('you may want to pip install "jina[prettytable]" for '
                               'better visualization')
        # poorman solution
        table = []

        def add_row(x):
            for h, y in zip(header, x):
                table.append(f'{h}\n{y}\n{"-" * 10}')

        def visualize(x):
            print('\n'.join(x))

    for route in routes:
        status_icon = '🟢'
        if route.status.code == jina_pb2.Status.ERROR:
            status_icon = '🔴'
        elif route.status.code == jina_pb2.Status.ERROR_CHAINED:
            status_icon = '⚪'

        add_row([f'{status_icon} {route.pod}',
                 f'{route.start_time.ToMilliseconds() - routes[0].start_time.ToMilliseconds()}ms',
                 fill(''.join(route.status.exception.stacks[-stack_limit:]), width=50,
                      break_long_words=False, replace_whitespace=False)])

    visualize(table)
