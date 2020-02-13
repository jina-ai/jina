import sys
import time

from termcolor import colored


class ProgressBar:
    """A simple progress bar

    Example:

        .. highlight:: python
        .. code-block:: python

            with ProgressBar('loop'):
                do_busy()
    """

    def __init__(self, bar_len: int = 20, task_name: str = ''):
        """

        :param bar_len: total length of the bar
        :param task_name: the name of the task, will be displayed in front of the bar
        """
        self.bar_len = bar_len
        self.task_name = task_name
        self.proc_doc = 0

    def update(self, progress: int = None) -> None:
        """ Increment the progress bar by one unit

        :param progress: the number of unit to increment
        """
        self.num_bars += 1
        sys.stdout.write('\r')
        elapsed = time.perf_counter() - self.start_time
        elapsed_str = colored('elapsed', 'yellow')
        speed_str = colored('batch', 'yellow')
        num_bars = self.num_bars % self.bar_len
        num_bars = self.bar_len if not num_bars and self.num_bars else max(num_bars, 1)
        if progress:
            self.proc_doc += progress

        sys.stdout.write(
            '{:>10} [{:<{}}]  {:>8}: {:3.1f}s  {:>8}: {:>8} @ {:3.1f}/s '.format(
                colored(self.task_name, 'cyan'),
                colored('=' * num_bars, 'green'),
                self.bar_len + 9,
                elapsed_str,
                elapsed,
                speed_str,
                self.num_bars,
                self.num_bars / elapsed,
            ))
        if num_bars == self.bar_len:
            sys.stdout.write('\n')
        sys.stdout.flush()

    def __enter__(self):
        self.start_time = time.perf_counter()
        self.num_bars = -1
        self.proc_doc = 0
        self.update()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.write('\t%s\n' % colored('done!', 'green'))
